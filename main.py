import saltwatch as sw

sw.load_persistent_data()
print(sw.player_id_dict, sw.player_name_dict)

p1_id, p2_id = sw.get_match_data()

sw.save_persistent_data()
sw.load_persistent_data()
print(sw.player_id_dict, sw.player_name_dict)

