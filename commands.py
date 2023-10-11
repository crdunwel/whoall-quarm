def generate_commands(start_level, end_level, start_page=1):
    classes = [
        ("Bard", "bard", "BRD"),
        ("Cleric", "cleric", "CLR"),
        ("Druid", "druid", "DRD"),
        ("Enchanter", "enchanter", "ENC"),
        ("Magician", "magician", "MAG"),
        ("Monk", "monk", "MNK"),
        ("Necromancer", "necromancer", "NEC"),
        ("Paladin", "paladin", "PAL"),
        ("Ranger", "ranger", "RNG"),
        ("Rogue", "rogue", "ROG"),
        ("Shadow Knight", "shadow", "SK"),
        ("Shaman", "shaman", "SHA"),
        ("Warrior", "warrior", "WAR"),
        ("Wizard", "wizard", "WIZ")
    ]

    commands = []

    page = start_page
    btn = 1
    line_num = 1

    lvl = start_level
    while lvl <= end_level:
        for class_long_name, cmd_name, btn_name in classes:

            if line_num == 1:  # If it's the first line, also append the button name
                if lvl <= 23:
                    lvl_in_name = f"{lvl}-{lvl+1}"
                else:
                    lvl_in_name = f"{lvl}"
                commands.append(f"Page{page}Button{btn}Name={btn_name} {lvl_in_name}")
                commands.append(f"Page{page}Button{btn}Color=0")


            if lvl <= 23:
                line_cmd = f"/pause 20, /who all {lvl} {lvl+1} {cmd_name}"
            else:
                line_cmd = f"/pause 20, /who all {lvl} {cmd_name}"

            commands.append(f"Page{page}Button{btn}Line{line_num}={line_cmd}")
            line_num += 1

            if line_num > 5:  # Reset the line number and increment the button number
                line_num = 1
                btn += 1

                if btn > 12:  # If button exceeds 12, move to the next page
                    page += 1
                    btn = 1

        if lvl <= 23:
            lvl += 2
        else:
            lvl += 1

    return commands

start_level = 1
end_level = 50
start_page = 2
commands = generate_commands(start_level, end_level, start_page)
for cmd in commands:
    print(cmd)