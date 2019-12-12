# created on 5 December 2019

surface = 0
underground = 0


def set_world_heights(h):
    global surface, underground
    surface = h // 2
    underground = h * 2 // 3
