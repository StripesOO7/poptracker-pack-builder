def generalized_rule_extractor(base_list: [str], delimiter1: str, delimiter2: str):
    """
    try's to open a possibly provided file containing the used logic for the AP-rando.
    for now, it reads the file and only looks for lambda rules. may change later to get expanded to lists/dicts but
    that's for another day.
    try's to split the rules into their intended and correct order. () > and > or
    after splitting it recombines them via vector/matrix multiplication to create ever possible permutation of rules.
    writes the extracted rules into a file as backup.
    """
    try:
        x = " | ".join(" + ".join(base_list.split(delimiter1)).split(delimiter2)).split(
            " | "
        )

        for iter, sub_list in enumerate(x):
            if " + " in sub_list:
                x[iter] = sub_list.split("+")
            else:
                x[iter] = [sub_list]

            for sub_iter, code in enumerate(x[iter]):
                if '"' in code:
                    search = '"'
                elif "'" in code:
                    search = "'"
                else:
                    continue
                x[iter][sub_iter] = code[code.index(search) + 1 : code.index(search)]
    except:
        x = base_list
    return list(itertools.product(*x))  # list cross multiplication to generate every


def slice_at_brackets(list_to_slice: []):
    lbracket = [
        j + 1 for j in range(len(list_to_slice)) if list_to_slice.startswith("(", j)
    ]
    rbracket = [
        j + 1 for j in range(len(list_to_slice)) if list_to_slice.startswith(")", j)
    ]
    if len(lbracket) == len(rbracket) - 1:
        rbracket.pop()
    lcount = 1
    rcount = 0
    stack = [lbracket[lcount - 1]]
    lastslice = 0
    temp = []
    while lcount < len(lbracket) and rcount < len(lbracket):
        # print("while", lcount, rcount)
        if len(stack) == 0 and lcount > 0 and rcount > 0:
            slice = rbracket[rcount]
            if lcount == len(lbracket):
                # print(temp)
                temp.append(list_to_slice[lastslice:])
            else:
                # print(temp)
                # print(rbracket[rcount], lbracket[lcount])
                if " or " in list_to_slice[lbracket[lcount] : rbracket[rcount]]:
                    temp.append(list_to_slice[lastslice : slice - 2])
                    lastslice = slice
                # else:
                #     # print(f'logic_temp[{i}][1]', lastslice, logic_temp[i][1][lastslice:])
                #     temp.append(logic_temp[i][1][lastslice:])

            stack.append(lbracket[lcount])
            lcount += 1
        else:
            if lbracket[lcount] < rbracket[rcount]:
                stack.append(lbracket[lcount])
                lcount += 1
            else:
                stack.pop()
                rcount += 1
    # lbracket = [j + 1 for j in range(len(list_to_slice)) if list_to_slice.startswith('(', j)]
    # rbracket = [j + 1 for j in range(len(list_to_slice)) if list_to_slice.startswith(')', j)]
    # if len(rbracket) == len(lbracket) - 1:
    #     lbracket.pop()
    # lcount = 1
    # rcount = 0
    # stack = [lbracket[lcount - 1]]
    # lastslice = 0
    # temp = []
    # while lcount < len(lbracket) - 1 and rcount < len(lbracket) - 1:
    #     if len(stack) == 0 and lcount > 0 and rcount > 0:
    #         slice = (lbracket[lcount] + rbracket[rcount]) // 2
    #         if not lcount == len(lbracket)-1:
    #             temp.append(list_to_slice[lastslice:slice])
    #         else:
    #             temp.append(list_to_slice[lastslice:])
    #         lastslice = slice
    #         stack.append(lbracket[lcount])
    #         lcount += 1
    #     else:
    #         if lbracket[lcount] < rbracket[rcount]:
    #             stack.append(lbracket[lcount])
    #             lcount += 1
    #         else:
    #             stack.pop()
    #             rcount += 1
    return temp


def extract_logic():
    """1 location             2+ rules, (if multiple lambdas then more lists else sublists in position 2
    ###     logic_temp[i] layout: [ [] ,                   [ [ ] , [ ] ], [ ], [ [ ] , [ ] ] ]
                            location_str    lambda            and    or   or       and
    """
    global logic
    logic_temp = []
    logic_dict = {}
    file_path = filedialog.askopenfilename()
    if not file_path == "":
        with open(file_path) as logic_extract:
            temp = logic_extract.read().split("\n")
            for i in temp:
                if " lambda " in i.lower():
                    logic_temp.append(
                        i.split("lambda")
                    )  # """results in a list containing tuples of [location_string,

            for i, test in enumerate(logic_temp):
                # i = 81
                if not "(" in logic_temp[i][1] and not ")" in logic_temp[i][1]:
                    logic_temp[i][1] = []
                else:
                    temp = slice_at_brackets(logic_temp[i][1])
                    if not len(temp) == 0:
                        # print(temp)
                        logic_temp[i][1] = temp

                    if type(logic_temp[i][1]) == list:
                        for counter, _ in enumerate(logic_temp[i][1]):

                            logic_temp[i][1][counter] = generalized_rule_extractor(
                                base_list=logic_temp[i][1][counter],
                                delimiter1=" or",
                                delimiter2=" and ",
                            )

                    else:
                        logic_temp[i][1] = generalized_rule_extractor(
                            base_list=logic_temp[i][1],
                            delimiter1=" or",
                            delimiter2=" and ",
                        )

                    if '"' in test[0]:
                        search = '"'
                    elif "'" in test[0]:
                        search = "'"
                    else:
                        continue
                    logic_temp[i][0] = test[0][
                        test[0].index(search) + 1 : test[0].index(search)
                    ]

            for i, _ in enumerate(logic_temp):
                # print("test")
                for j, _ in enumerate(logic_temp[i][:-2]):
                    logic_temp[i][j] = logic_temp[i][j].strip('"').strip("'")

    with open(read_file_path + "/logic_backup.txt", "w") as logic_backup:
        for line in logic_temp:
            logic_backup.write(f"{line}\n")
    delimiter = ['", "', "', '", '",', "',", " - ", ": ", ") "]

    for index, _ in enumerate(logic_temp):
        for spacer in delimiter:
            if spacer in logic_temp[index][0]:
                logic_temp[index][0] = logic_temp[index][0].replace(f"{spacer}", "/")

            else:
                logic_temp[index][0] = logic_temp[index][0]
        logic_temp[index][0] = list(dict.fromkeys(logic_temp[index][0].split("/")))

    region_temp = []
    for i, _ in enumerate(logic_temp):
        region_temp.append(logic_temp[i][0][0])
    region_temp_set = set(region_temp)
    logic_dict = {e: {} for e in region_temp_set}
    for index, _ in enumerate(logic_temp):
        sub_list = logic_temp[index][0]
        if len(logic_temp[index][1]) == 1:
            print(logic_temp[index][1], logic_temp[index][1][0])
            logic_temp[index][1] = logic_temp[index][1][0]
        if len(sub_list) == 3:
            try:
                logic_dict[sub_list[0]][sub_list[1]].update(
                    {sub_list[2]: logic_temp[index][1]}
                )
            except:
                logic_dict[sub_list[0]].update({sub_list[1]: {}})
                logic_dict[sub_list[0]][sub_list[1]].update(
                    {sub_list[2]: logic_temp[index][1]}
                )
        elif len(sub_list) == 2:
            try:
                logic_dict[sub_list[0]].update({sub_list[1]: logic_temp[index][1]})
            except:
                pass
        elif len(sub_list) == 1:
            try:
                logic_dict.update({sub_list[0]: logic_temp[index][1]})
            except:
                pass
    return logic_dict
