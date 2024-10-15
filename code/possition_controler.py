
class Poss_Fix:
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.x_axis = width//2
        self.y_axis = 0

    def set_pos(self, img_ht, img_wt, x_pos, y_pos=0):
        if x_pos != 0:
            player_x = int((x_pos/img_wt)*self.width)
        else:
            player_x = 0


        return player_x




