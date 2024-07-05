from dataclasses import dataclass

@dataclass
class MyGlobalData:
    game_id_counter: int


my_global_vars = MyGlobalData(0)