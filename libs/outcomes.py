
class Outcomes:
    async def get_3way_opposite_type(self, type_, ps3838):
        oppose_type_1, oppose_type_2 = '', ''
        if type_ == '1':
            oppose_type_1 = 'X'
            oppose_type_2 = '2'
        elif type_ == 'X':
            oppose_type_1 = '1'
            oppose_type_2 = '2'
        elif type_ == '2':
            oppose_type_1 = '1'
            oppose_type_2 = 'X'
        if type_ == '1X':
            oppose_type_1 = '12'
            oppose_type_2 = 'X2'
        elif type_ == '12':
            oppose_type_1 = '1X'
            oppose_type_2 = 'X2'
        elif type_ == 'X2':
            oppose_type_1 = '1X'
            oppose_type_2 = '12'
        if type_ == '1H1':
            oppose_type_1 = '1HX'
            oppose_type_2 = '1H2'
        elif type_ == '1HX':
            oppose_type_1 = '1H1'
            oppose_type_2 = '1H2'
        elif type_ == '1H2':
            oppose_type_1 = '1H1'
            oppose_type_2 = '1HX'
        if type_ == '1H1X':
            oppose_type_1 = '1H12'
            oppose_type_2 = '1HX2'
        elif type_ == '1H12':
            oppose_type_1 = '1H1X'
            oppose_type_2 = '1HX2'
        elif type_ == '1HX2':
            oppose_type_1 = '1H1X'
            oppose_type_2 = '1H12'
        return oppose_type_1, oppose_type_2

    async def get_2way_opposite_type(self, type_, line):
        oppose_type, oppose_line = '', ''
        if type_ == 'H1':
            oppose_type = 'H2'
            if line[:1] == '-':
                oppose_line = line[1:]
            else:
                if line == '0.0':
                    oppose_line = line
                else:
                    oppose_line = f'-{line}'
        elif type_ == 'H2':
            oppose_type = 'H1'
            if line[:1] == '-':
                oppose_line = line[1:]
            else:
                if line == '0.0':
                    oppose_line = line
                else:
                    oppose_line = f'-{line}'
        if type_ == '1HH1':
            oppose_type = '1HH2'
            if line[:1] == '-':
                oppose_line = line[1:]
            else:
                if line == '0.0':
                    oppose_line = line
                else:
                    oppose_line = f'-{line}'
        elif type_ == '1HH2':
            oppose_type = '1HH1'
            if line[:1] == '-':
                oppose_line = line[1:]
            else:
                if line == '0.0':
                    oppose_line = line
                else:
                    oppose_line = f'-{line}'
        elif type_ == 'O':
            oppose_type = 'U'
            oppose_line = line
        elif type_ == 'U':
            oppose_type = 'O'
            oppose_line = line
        elif type_ == '1HO':
            oppose_type = '1HU'
            oppose_line = line
        elif type_ == '1HU':
            oppose_type = '1HO'
            oppose_line = line
        elif type_ == '1':
            oppose_type = '2'
            oppose_line = line
        elif type_ == '2':
            oppose_type = '1'
            oppose_line = line
        # elif type_ == '1H1':
        #     oppose_type = '1H2'
        #     oppose_line = line
        # elif type_ == '1H2':
        #     oppose_type = '1H1'
        #     oppose_line = line
        return oppose_type, oppose_line

    async def get_2way_opposite_odds(self, type_, line, ps3838):
        opposite_type, opposite_line = await self.get_2way_opposite_type(type_, line)
        opposite_odds = [x['odds'] for x in ps3838['converted_markets']
                         if x['type'] == opposite_type and x['line'] == opposite_line][0]
        return opposite_odds

    async def get_3way_opposite_odds(self, type_, ps3838):
        opposite_type_1, opposite_type_2 = await self.get_3way_opposite_type(type_, ps3838)
        opposite_odds_1 = [x['odds'] for x in ps3838['converted_markets'] if x['type'] == opposite_type_1][0]
        opposite_odds_2 = [x['odds'] for x in ps3838['converted_markets'] if x['type'] == opposite_type_2][0]
        return opposite_odds_1, opposite_odds_2

    async def get_margin(self, ps, ps3838):
        if ps['type_name'] in ['1X2', 'Double Chance', 'First Half 1X2']:
            opposite_odds_1, opposite_odds_2 = await self.get_3way_opposite_odds(ps['type'], ps3838)
            margin = (1 / float(ps['odds']) + 1 / float(opposite_odds_1) + 1 / float(opposite_odds_2)) - 1
            n = 3
        else:
            opposite_odds = await self.get_2way_opposite_odds(ps['type'], ps['line'], ps3838)
            margin = (1 / float(ps['odds']) + 1 / float(opposite_odds)) - 1
            n = 2
        return margin, n
