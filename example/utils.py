import itertools
import sys

import attr
import pygame

from ecs.engine import Engine
from example.components import Floor, Renderable, Player
from example.settings import MAP_SIZE, RESOLUTION, FPS, CAPTION


@attr.s(slots=True)
class App:
    window = attr.ib()
    clock = attr.ib()
    rect_list = attr.ib(default=list())

    def display_fps(self):
        caption = "{} - FPS: {:.2f}".format(CAPTION, self.clock.get_fps())
        pygame.display.set_caption(caption)


def setup_app() -> App:
    pygame.init()
    window = pygame.display.set_mode(RESOLUTION)
    clock = pygame.time.Clock()
    return App(window=window, clock=clock)


def setup_map(engine: Engine) -> None:
    map_x, map_y = MAP_SIZE
    for x, y in itertools.product(range(map_x), range(map_y)):
            if x not in [0, map_x - 1] and y not in [0, map_y - 1]:
                continue
            block = engine.create_entity()
            block_component = Floor(walkable=False)
            renderable_component = Renderable(
                path='block.png',
                posx=x,
                posy=y,
            )
            engine.add_component(block, [block_component, renderable_component])
    player = engine.create_entity()
    player_component = Player()
    player_sprite = Renderable(
        path='player.png',
        posx=map_x/2,
        posy=map_y/2,
    )
    engine.add_component(player, [player_component, player_sprite])


def game_loop(engine: Engine, app: App):
    done = False
    while not done:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
        engine.process(events=events)
        app.clock.tick(FPS)
        app.display_fps()
    pygame.quit()
    sys.exit()