import sys
import pygame
import numpy
from pygame.sprite import Sprite, Group
from random import shuffle
from functools import cmp_to_key

from settings import Settings
from card import Card
from board import Board
from button import Button
from game_stage import GameStage

class DaTongSolitaire:
    """管理游戏资源和行为的类"""
    
    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        Settings.screen_height = self.screen.get_rect().height
        Settings.screen_width = self.screen.get_rect().width
        Settings.init()
        pygame.display.set_caption("大通纸牌")
        self.game_stage = GameStage.start_menu
        
        self.play_button = Button(
            msg=Settings.play_button_msg,
            width=Settings.play_button_width,
            height=Settings.play_button_height,
            button_color=Settings.play_button_color,
            text_color=Settings.play_button_text_color,
            font_size=Settings.play_button_font_size
        )
        self.exit_button = Button(
            msg=Settings.exit_button_msg,
            width=Settings.exit_button_width,
            height=Settings.exit_button_height,
            button_color=Settings.exit_button_color,
            text_color=Settings.exit_button_text_color,
            font_size=Settings.exit_button_font_size
        )
        self.exit_button.rect.y = self.play_button.rect.y + Settings.start_menu_button_spacing + Settings.play_button_height
        self.board = Board(self)
        self.hand: list[Group] = [Group(), Group(), Group(), Group()]
        self.trashed_cards: list[Group] = [Group(), Group(), Group(), Group()]
        self.played_cards_less_7: list[list[Card]] = [[], [], [], []]
        self.played_cards_greater_7: list[list[Card]] = [[], [], [], []]
        self.played_cards_7: list[list[Card]] = [[], [], [], []]
        self.score:list[int] = [0, 0, 0, 0]
        
        # 生成卡牌，洗牌并发牌
        cards = []
        for i in range(4):
            for j in range(1, 13+1):
                cards.append((i, j))
        shuffle(cards)
        for i in range(4):
            hand_cards = cards[i*13:(i+1)*13]
            hand_cards.sort(key=cmp_to_key(Card.cmp))
            if (0, 7) in hand_cards:
                start_player = i
            for card_tuple in hand_cards:
                Card(*card_tuple, self.hand[i])
        
        # 状态
        self.focused_card: Card = None
        self.playable_cards: list[tuple] = [(0, 7)]   # 开局只能出黑桃7
        self.start_player = start_player
        self.current_player = start_player
        self.can_play_card = True   # 根据规则，当前玩家是否能出牌
        self.end_turn = False
    
    def run_game(self):
        """开始游戏的主循环"""
        while True:
            self._check_events()
            self._update_objects()
            self._update_screen()
            self.clock.tick(30)

    def _update_objects(self):
        """更新游戏中的物体属性等"""
        if self.game_stage == GameStage.start_menu:
            pass
        elif self.game_stage == GameStage.playing:
            self.board.update()
            self._update_cards()
            if self.end_turn:
                self._next_turn()

    def _check_events(self):
        """响应按键和鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if self.game_stage == GameStage.start_menu:
                        # 检测是否点击了按钮
                        mouse_pos = pygame.mouse.get_pos()
                        if self.play_button.rect.collidepoint(mouse_pos):
                            self.game_stage = GameStage.playing
                        elif self.exit_button.rect.collidepoint(mouse_pos):
                            sys.exit()
                    elif self.game_stage == GameStage.playing:
                        if self.focused_card:
                            self._on_focused_card_clicked()

    def _next_turn(self):
        """即将进入下一个玩家的回合"""
        self.end_turn = False
        # 判断是否游戏结束
        # 如果所有玩家均没有手牌了则游戏结束
        if not any(self.hand):
            self._end_game()
            return
        
        # 更新当前玩家 和 当前玩家是否可出牌的状态
        self.current_player = (self.current_player + 1) % 4
        self.can_play_card = False
        for card in self.hand[self.current_player]:
            if card.info in self.playable_cards:
                self.can_play_card = True
                break
    
    def _end_game(self):
        """游戏结束时的结算"""
        score_multiply_power = 1
        # 弃牌点数加总
        points = [0, 0, 0, 0]
        for i, player_trashed_cards in enumerate(self.trashed_cards):
            for card in player_trashed_cards:
                points[i] += card.rank
        # 后手玩家惩罚点数
        for i in range(4):
            points[(self.start_player + i) % 4] += i / 10
        # 排序得出分数
        sorted_player_points_pairs = sorted(enumerate(points), key=lambda x: x[1])
        if sorted_player_points_pairs[0][1] < 1:
            score_multiply_power = 2   # 大通
        for i, pair in enumerate(sorted_player_points_pairs):
            self.score[pair[0]] += Settings.base_score[i] * score_multiply_power
    
    def _on_focused_card_clicked(self):
        """当聚焦的卡牌被点击时"""
        card = self.focused_card
        # 如果聚焦的卡牌为当前玩家的卡牌并且可以打出
        if card.info in self.playable_cards and card in self.hand[self.current_player]:
            self._play_card(card)
            
        # 如果聚焦的卡牌为当前玩家的卡牌，但是当前玩家无牌可出，则被点击的卡牌视为弃牌
        elif not self.can_play_card and card in self.hand[self.current_player]:
            self._discard_card(card)
            
        else:
            print("不能打出此牌！")
    
    def _play_card(self, card: Card):
        """当前玩家打出指定的卡牌"""
        # 将此牌从手中移动到场上
        if card.rank < 7:
            self.played_cards_less_7[card.suit].append(card)
        elif card.rank > 7:
            self.played_cards_greater_7[card.suit].append(card)
        else:
            self.played_cards_7[card.suit].append(card)
        self.hand[self.current_player].remove(card)
        
        # 更新可打出牌的列表
        self.playable_cards.remove(card.info)
        if card.info == (0, 7):
            for i in range(1, 4):
                self.playable_cards.append((i, 7))
            self.playable_cards.append((0, 6))
            self.playable_cards.append((0, 8))
        elif card.rank == 7:
            self.playable_cards.append((card.suit, 6))
            self.playable_cards.append((card.suit, 8))
        elif card.rank == 1 or card.rank == 13:
            pass
        elif card.rank < 7:
            self.playable_cards.append((card.suit, card.rank - 1))
        elif card.rank > 7:
            self.playable_cards.append((card.suit, card.rank + 1))
        else:
            raise Exception("We met a mistake in updating playable_cards!")
        
        self.end_turn = True
    
    def _discard_card(self, card: Card):
        """当前玩家弃置指定的卡牌"""
        # 将此牌从手中移动到弃牌堆
        self.trashed_cards[self.current_player].add(card)
        self.hand[self.current_player].remove(card)
        
        # 改变被弃牌的UI
        pixels = pygame.surfarray.pixels3d(card.image)
        pixels //= 2
        
        self.end_turn = True
            

    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
        self.screen.fill(Settings.bg_color)
        if self.game_stage == GameStage.start_menu:
            self.play_button.blitme()
            self.exit_button.blitme()
        elif self.game_stage == GameStage.playing:
            self.board.blitme()
            self._draw_cards()
        
        pygame.display.flip()
    
    def _update_cards(self):
        """更新所有卡牌的图像"""
        
        #  设置我的手牌位置
        left_margin = (Settings.screen_width
                       - (len(self.hand[0])-1) * Settings.hand_card_x_spacing
                       - Settings.hand_card_width) // 2
        for i, card in enumerate(self.hand[0]):
            card.rect.left = left_margin + i * Settings.hand_card_x_spacing
            card.rect.bottom = Settings.screen_height + 0.6 * Settings.hand_card_height
        
        left_margin += len(self.hand[0]) * Settings.hand_card_x_spacing
        for i, card in enumerate(self.trashed_cards[0]):
            card.rect.left = left_margin + i * Settings.hand_card_x_spacing
            card.rect.bottom = Settings.screen_height + 0.6 * Settings.hand_card_height
        
        # 设置右侧玩家手牌位置
        top_margin = (Settings.screen_height
                       - (len(self.hand[1])-1) * Settings.hand_card_y_spacing
                       - Settings.hand_card_height) // 2
        for i, card in enumerate(self.hand[1]):
            card.rect.top = top_margin + i * Settings.hand_card_y_spacing
            card.rect.right = Settings.screen_width + 0.6 * Settings.hand_card_width
        
        top_margin += len(self.hand[1]) * Settings.hand_card_y_spacing
        for i, card in enumerate(self.trashed_cards[1]):
            card.rect.top = top_margin + i * Settings.hand_card_y_spacing
            card.rect.right = Settings.screen_width + 0.6 * Settings.hand_card_width
        
        # 设置对侧玩家的手牌位置
        right_margin = (Settings.screen_width
                       - (len(self.hand[2])-1) * Settings.hand_card_x_spacing
                       - Settings.hand_card_width) // 2
        for i, card in enumerate(self.hand[2]):
            card.rect.right = Settings.screen_width - (right_margin + i * Settings.hand_card_x_spacing)
            card.rect.top = 0 - 0.6 * Settings.hand_card_height
        
        right_margin += len(self.hand[2]) * Settings.hand_card_x_spacing
        for i, card in enumerate(self.trashed_cards[2]):
            card.rect.right = Settings.screen_width - (right_margin + i * Settings.hand_card_x_spacing)
            card.rect.top = 0 - 0.6 * Settings.hand_card_height
        
        # 设置左侧玩家手牌位置
        top_margin = (Settings.screen_height
                       - (len(self.hand[3])-1) * Settings.hand_card_y_spacing
                       - Settings.hand_card_height) // 2
        for i, card in enumerate(self.hand[3]):
            card.rect.top = top_margin + i * Settings.hand_card_y_spacing
            card.rect.left = 0 - 0.6 * Settings.hand_card_width
        
        top_margin += len(self.hand[3]) * Settings.hand_card_y_spacing
        for i, card in enumerate(self.trashed_cards[3]):
            card.rect.top = top_margin + i * Settings.hand_card_y_spacing
            card.rect.left = 0 - 0.6 * Settings.hand_card_width
            
        # 设置场上卡牌位置
        for i in range(4):
            for j, card in enumerate(reversed(self.played_cards_greater_7[i])):
                card.rect.centerx = Settings.field_x_margin + i * Settings.field_x_spacing
                n = len(self.played_cards_greater_7[i])
                card.rect.centery = Settings.screen_height // 2 - (n-j) * Settings.field_y_spacing

        for i in range(4):
            for j, card in enumerate(self.played_cards_7[i]):
                card.rect.centerx = Settings.field_x_margin + i * Settings.field_x_spacing
                card.rect.centery = Settings.screen_height // 2
        
        for i in range(4):
            for j, card in enumerate(self.played_cards_less_7[i]):
                card.rect.centerx = Settings.field_x_margin + i * Settings.field_x_spacing
                card.rect.centery = Settings.screen_height // 2 + (j+1) * Settings.field_y_spacing
        
        # 检测鼠标是否聚焦手牌
        self.focused_card = None
        pos = pygame.mouse.get_pos()
        for i, hand in enumerate(self.hand):
            for card in reversed(hand.sprites()):
                if card.rect.collidepoint(pos):
                    self.focused_card = card
                    if i == 0:
                        card.rect.bottom = Settings.screen_height
                    elif i == 1:
                        card.rect.right = Settings.screen_width
                    elif i == 2:
                        card.rect.top = 0
                    elif i == 3:
                        card.rect.left = 0
                    else:
                        raise Exception("Too many hand!")
                    break
        
    def _draw_cards(self):
        """在屏幕上绘制所有卡牌"""
        # 显示场上卡牌
        for i in range(4):
            for card in reversed(self.played_cards_greater_7[i]):
                self.screen.blit(card.image, card.rect)

        for i in range(4):
            for card in self.played_cards_7[i]:
                self.screen.blit(card.image, card.rect)
        
        for i in range(4):
            for card in self.played_cards_less_7[i]:
                self.screen.blit(card.image, card.rect)
        
        # 显示手牌
        for hand in self.hand:
            for card in hand:
                if card.info in self.playable_cards and card in self.hand[self.current_player]:
                    frame_rect = card.rect.inflate(
                            Settings.playable_card_frame_width,
                            Settings.playable_card_frame_width
                        )
                    pygame.draw.rect(
                            self.screen,
                            Settings.playable_card_frame_color,
                            frame_rect,
                            width=Settings.playable_card_frame_width,
                            border_radius=Settings.playable_card_frame_border_radius
                        )
                card.blitme()
        
        # 显示弃牌堆
        for player_trashed_cards in self.trashed_cards:
            player_trashed_cards.draw(self.screen)


if __name__ == '__main__':
    game = DaTongSolitaire()
    game.run_game()