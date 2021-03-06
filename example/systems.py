import pygame

from ecs.system import ISystem
from example.components import Renderable, Player, Fruit, Wall, Tail
from example.enums import DirectionEnum, ContextEnum
from example.utils import spawn_fruit, attach_tail


class RenderableSystem(ISystem):
    def process(self, *args, **kwargs):
        self.engine.app.window.fill((0, 0, 0))
        self.engine.context[ContextEnum.RENDERABLE] = list()
        for entity, renderable in self.engine.get_components(Renderable):
            self.engine.app.window.blit(
                renderable.sprite.image,
                renderable.sprite.rect
            )
            self.update_position(entity, renderable)
        pygame.display.update()
        pygame.display.flip()

    def update_position(self, entity, renderable):
        self.engine.context[ContextEnum.RENDERABLE].append(
            (entity, renderable.sprite)
        )


class MovePlayerSystem(ISystem):
    def process(self, events):
        _, player = next(self.engine.get_components(Player))
        for event in events:
            if event.type == pygame.KEYDOWN:
                direction = None
                if (event.key == pygame.K_UP and
                        player.direction != DirectionEnum.DOWN):
                    direction = DirectionEnum.UP
                if (event.key == pygame.K_DOWN and
                        player.direction != DirectionEnum.UP):
                    direction = DirectionEnum.DOWN
                if (event.key == pygame.K_RIGHT and
                        player.direction != DirectionEnum.LEFT):
                    direction = DirectionEnum.RIGHT
                if (event.key == pygame.K_LEFT and
                        player.direction != DirectionEnum.RIGHT):
                    direction = DirectionEnum.LEFT
                self.change_direction(player, direction)

        self.resolve_collision(player, player.head['renderable'])
        self.move_head(player)
        self.move_tail(player)

    def change_direction(self, player, direction):
        if not direction:
            return
        try:
            tail_position = \
                player.tail[1]['renderable'].sprite.get_position(as_int=True)
            head_position = \
                player.head['renderable'].sprite.get_position(as_int=True)
            result = [
                a-b for a, b in zip(tail_position, head_position)
            ]
            result = [a + b for a, b in zip(result, direction)]
        except IndexError:
            player.direction = direction
        else:
            if all(result):
                player.direction = direction

    def collided_entity(self, renderable):
        context_renderables = self.engine.get_context_item(
            ContextEnum.RENDERABLE) or list()
        for entity, sprite in context_renderables:
            if (renderable.sprite.is_collided_with(sprite) and
                    renderable.sprite is not sprite):
                return entity

    def attach_tail(self, player):
        return attach_tail(self.engine, player)

    def move_head(self, player):
        direction_x, direction_y = player.direction

        head_renderable = player.head['renderable']
        head_component = player.head['component']

        head_renderable.sprite.move_position(
            direction_x * player.speed,
            direction_y * player.speed,
        )

        actual_position = head_renderable.sprite.get_position(as_int=True)
        component_position = head_component.old_position
        result = [abs(a-b) for a, b in zip(actual_position, component_position)]
        if any(filter(lambda x: x > 1, result)) or all(result):
            head_component.old_position = (
                [a-b for a, b in zip(actual_position, player.direction)]
            )

    def move_tail(self, player):
        try:
            for i, tail in enumerate(player.tail[1:]):
                head_position = player.tail[i]['component'].old_position
                sprite = tail['renderable'].sprite
                tail_position = sprite.get_position(as_int=True)

                if tail_position == head_position:
                    break

                tail['component'].old_position = tail_position
                sprite.set_position(*head_position)
        except KeyError:
            pass

    def resolve_collision(self, player, renderable):
        entity = self.collided_entity(renderable)
        if not entity:
            return

        entity_components = self.engine.get_entity_components(entity)
        if not entity_components:  # already dead entity
            return

        if entity_components.get(Fruit):
            self.engine.remove_entity(entity)
            self.attach_tail(player)
        elif {Wall, Tail} & entity_components.keys():
            player.speed = 0


class FruitSystem(ISystem):
    def process(self, *args, **kwargs):
        fruit_ec = next(self.engine.get_components((Fruit, Renderable)), None)
        if not fruit_ec:
            self.respawn_fruit()

    def respawn_fruit(self):
        spawn_fruit(self.engine)
