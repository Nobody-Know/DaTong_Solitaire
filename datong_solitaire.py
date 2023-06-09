import sys
import pygame
import numpy
from pygame.sprite import Sprite, Group
from pygame.event import Event
from pygame.mixer import Sound
from random import shuffle, choice, random
from functools import cmp_to_key

from singleton import Singleton
from settings import Settings
from card import Card
from board import Board
from button import Button
from game_stage import GameStage
from start_menu import StartMenu
from game_over_menu import GameOverMenu
from ai_agent import AiAgent, AiAgentRandom, AiAgentNormal
from window import Window
from rule_window import RuleWindow
from exit_window import ExitWindow
from stop_game_window import StopGameWindow
from utils import darken

class DaTongSolitaire(Singleton):
    """管理游戏资源和行为的类"""
    
    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings = Settings(game=self)
        pygame.display.set_caption("大通纸牌")
        self.game_stage = GameStage.start_menu
        self.score:list[int] = [0, 0, 0, 0]
        self.buttons = Group()
        self.start_menu = StartMenu(self)
        Card._load_card_back_image()
        self.ai_act_event = pygame.event.custom_type()
        self.windows: list[Window] = []
        pygame.mixer.init()
        self.start_menu_music = Sound(choice(self.settings.start_menu_music))
        self.start_menu_music.play()
        self.discard_sound = Sound('music/音效/要不起.mp3')
        self.discovered = False
    
    def new_game(self):
        """重置游戏的所有状态，以开始一场新的游戏"""
        pygame.mixer.fadeout(1000)
        self.game_stage = GameStage.playing
        self.board = Board()
        self.stop_button = Button(
            msg=self.settings.field.stop_button.msg,
            width=self.settings.field.stop_button.width,
            height=self.settings.field.stop_button.height,
            x=self.settings.field.stop_button.centerx,
            y=self.settings.field.stop_button.centery,
            button_color=self.settings.field.stop_button.color,
            font_size=self.settings.field.stop_button.font_size
        )
        self.hand: list[Group] = [Group(), Group(), Group(), Group()]
        self.trashed_cards: list[Group] = [Group(), Group(), Group(), Group()]
        self.played_cards_less_7: list[list[Card]] = [[], [], [], []]
        self.played_cards_greater_7: list[list[Card]] = [[], [], [], []]
        self.played_cards_7: list[list[Card]] = [[], [], [], []]
        # self.ai_player:list[AiAgent] = [AiAgentRandom(0), AiAgentRandom(1), AiAgentRandom(2), AiAgentRandom(3)]
        self.ai_player: list[AiAgent] = [AiAgentNormal(0), AiAgentNormal(1), AiAgentNormal(2), AiAgentNormal(3)]
        
        # 生成卡牌，洗牌并发牌
        cards = [(i, j) for i in range(4) for j in range(1, 13+1)]
        shuffle(cards)
        for i in range(4):
            hand_cards = cards[i*13:(i+1)*13]
            hand_cards.sort(key=cmp_to_key(Card.cmp))
            if (0, 7) in hand_cards:
                start_player = i
            for card_tuple in hand_cards:
                Card(*card_tuple, i, self.hand[i])
        
        # 将非己方手牌设置为不可见
        for i in range(1, 4):
            for card in self.hand[i]:
                card.to_invisible()
        
        # 状态
        self.focused_card: Card = None
        self.playable_cards: list[tuple] = [(0, 7)]   # 开局只能出黑桃7
        self.start_player = start_player
        self.current_player = start_player
        self.can_play_card = True   # 根据规则，当前玩家是否能出牌
        self.end_turn = False
        
        # 如果黑桃7在电脑玩家手中，则设置计时器
        if self.current_player != 0:
            pygame.time.set_timer(self.ai_act_event, self.settings.ai_act_interval, 4 - self.current_player)
        
    def new_test_game(self):
        """重置游戏的所有状态，以开始一场新的测试游戏"""
        self.game_stage = GameStage.testing
        self.board = Board()
        self.hand: list[Group] = [Group(), Group(), Group(), Group()]
        self.trashed_cards: list[Group] = [Group(), Group(), Group(), Group()]
        self.played_cards_less_7: list[list[Card]] = [[], [], [], []]
        self.played_cards_greater_7: list[list[Card]] = [[], [], [], []]
        self.played_cards_7: list[list[Card]] = [[], [], [], []]
        
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
                Card(*card_tuple, i, self.hand[i])
        
        # 状态
        self.focused_card: Card = None
        self.playable_cards: list[tuple] = [(0, 7)]   # 开局只能出黑桃7
        self.start_player = start_player
        self.current_player = start_player
        self.can_play_card = True   # 根据规则，当前玩家是否能出牌
        self.end_turn = False
    
    # def new_test_game_one_card_per_player(self):
    #     """重置游戏的所有状态，以开始一场新的测试游戏，测试游戏中每名玩家只有一张牌，以便快速测试游戏结束的场景"""
    #     self.game_stage = GameStage.testing
    #     self.board = Board()
    #     self.hand: list[Group] = [Group(), Group(), Group(), Group()]
    #     self.trashed_cards: list[Group] = [Group(), Group(), Group(), Group()]
    #     self.played_cards_less_7: list[list[Card]] = [[], [], [], []]
    #     self.played_cards_greater_7: list[list[Card]] = [[], [], [], []]
    #     self.played_cards_7: list[list[Card]] = [[], [], [], []]
        
    #     # 生成卡牌，洗牌并发牌
    #     cards = []
    #     for i in range(4):
    #         for j in range(1, 1+1):
    #             cards.append((i, j))
    #     shuffle(cards)
    #     for i in range(4):
    #         hand_cards = cards[i*1:(i+1)*1]
    #         hand_cards.sort(key=cmp_to_key(Card.cmp))
    #         start_player = 0
    #         for card_tuple in hand_cards:
    #             Card(*card_tuple, self.hand[i])
        
    #     # 状态
    #     self.focused_card: Card = None
    #     self.playable_cards: list[tuple] = [(0, 7)]   # 开局只能出黑桃7
    #     self.start_player = start_player
    #     self.current_player = start_player
    #     self.can_play_card = False   # 根据规则，当前玩家是否能出牌
    #     self.end_turn = False
    
    def run_game(self):
        """开始游戏的主循环"""
        while True:
            self._check_events()
            self._update_objects()
            self._update_screen()
            self.clock.tick(30)

    def _update_objects(self):
        """更新游戏中的物体属性等"""
        self.buttons.update()
        if self.game_stage == GameStage.start_menu:
            pass
        elif self.game_stage == GameStage.playing:
            self.board.update()
            self._update_cards()
            if self.end_turn:
                self._next_turn()
        elif self.game_stage == GameStage.testing:
            self.board.update()
            self._update_cards()
            if self.end_turn:
                self._next_turn()
        elif self.game_stage == GameStage.game_over_menu:
            self.game_over_menu.update()

    def _check_events(self):
        """响应按键和鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            # 对不同场景进行分类处理
            if self.windows:
                self._check_events_with_window(event, self.windows[-1])
            else:
                self._check_events_without_window(event)
            
            

    def _check_events_with_window(self, event: Event, window: Window):
        """有弹出窗口时的事件检查"""
        if isinstance(window, RuleWindow):
            self._check_events_with_rule_window(event, window)
        elif isinstance(window, ExitWindow):
            self._check_events_with_exit_window(event, window)
        elif isinstance(window, StopGameWindow):
            self._check_events_with_stop_game_window(event, window)
        else:
            raise Exception("Unknown window!")
            
    def _check_events_with_rule_window(self, event: Event, window: RuleWindow):
        """在规则窗口的事件检查"""
        # 如果左键点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            mouse_pos = pygame.mouse.get_pos()
            if window.exit_button.abs_rect.collidepoint(mouse_pos):
                self.game_stage = GameStage.start_menu
                self.windows.pop()
    
    def _check_events_with_exit_window(self, event: Event, window: ExitWindow):
        """在退出确认窗口的事件检查"""
        # 如果左键点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            mouse_pos = pygame.mouse.get_pos()
            if window.confirm_button.abs_rect.collidepoint(mouse_pos):
                sys.exit()
            elif window.cancel_button.abs_rect.collidepoint(mouse_pos):
                self.windows.pop()
                self._continue_game()
    
    def _check_events_with_stop_game_window(self, event: Event, window: StopGameWindow):
        """在游戏暂停窗口的事件检查"""
        # 如果左键点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            mouse_pos = pygame.mouse.get_pos()
            if window.replay_button.abs_rect.collidepoint(mouse_pos):
                self.windows.pop()
                self.new_game()
            elif window.continue_button.abs_rect.collidepoint(mouse_pos):
                self.windows.pop()
                self._continue_game()
            elif window.exit_button.abs_rect.collidepoint(mouse_pos):
                self.exit_confirm()
    
    def _check_events_without_window(self, event: Event):
        """无弹出窗口时的事件检查"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.exit_confirm()
                return
        if self.game_stage == GameStage.start_menu:
            self._check_events_in_start_menu(event)
        elif self.game_stage == GameStage.playing:
            self._check_events_in_game(event)
        elif self.game_stage == GameStage.testing:
            self._check_events_in_testing_game(event)
        elif self.game_stage == GameStage.game_over_menu:
            self._check_events_in_game_over_menu(event)
        else:
            # TODO
            pass
        
        # elif event.type == pygame.MOUSEBUTTONDOWN:
        #     if event.button == pygame.BUTTON_LEFT:
        #         if self.game_stage == GameStage.start_menu:
        #             # 检测是否点击了按钮
        #             mouse_pos = pygame.mouse.get_pos()
        #             if self.start_menu.play_button.rect.collidepoint(mouse_pos):
        #                 self.new_game()
        #             elif self.start_menu.rule_button.rect.collidepoint(mouse_pos):
        #                 self.open_rule()
        #             elif self.start_menu.exit_button.rect.collidepoint(mouse_pos):
        #                 sys.exit()
        #         elif self.game_stage == GameStage.rule:
        #             # TODO
        #             mouse_pos = pygame.mouse.get_pos()
        #             if self.windows[-1].exit_button.rect.collidepoint(mouse_pos):
        #                 self.game_stage = GameStage.start_menu
        #                 self.windows.pop()
        #         elif self.game_stage == GameStage.playing:
        #             if self.current_player == 0:
        #                 if self.focused_card:
        #                     self._on_focused_card_clicked()
        #         elif self.game_stage == GameStage.testing:
        #             if self.focused_card:
        #                 self._on_focused_card_clicked()
        #         elif self.game_stage == GameStage.game_over_menu:
        #             # TODO
        #             mouse_pos = pygame.mouse.get_pos()
        #             if self.game_over_menu.rect.collidepoint(mouse_pos):
        #                 mouse_pos = (
        #                         mouse_pos[0] - self.game_over_menu.rect.left,
        #                         mouse_pos[1] - self.game_over_menu.rect.top
        #                     )
        #                 if self.game_over_menu.replay_button.rect.collidepoint(mouse_pos):
        #                     self.new_game()
        #                 elif self.game_over_menu.exit_button.rect.collidepoint(mouse_pos):
        #                     sys.exit()
        # elif event.type == self.ai_act_event:
        #     if self.can_play_card:
        #         card = self.ai_player[self.current_player].get_card_to_play()
        #         self._play_card(card)
        #     else:
        #         card = self.ai_player[self.current_player].get_card_to_discard()
        #         self._discard_card(card)
    
    def _check_events_in_start_menu(self, event: Event):
        # 如果左键点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            mouse_pos = pygame.mouse.get_pos()
            if self.start_menu.play_button.rect.collidepoint(mouse_pos):
                self.new_game()
            elif self.start_menu.rule_button.rect.collidepoint(mouse_pos):
                self.open_rule()
            elif self.start_menu.exit_button.rect.collidepoint(mouse_pos):
                self.exit_confirm()
    
    def _check_events_in_game(self, event: Event):
        # 如果左键点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            mouse_pos = pygame.mouse.get_pos()
            if self.current_player == 0:
                if self.focused_card:
                    self._on_focused_card_clicked()
            if self.stop_button.abs_rect.collidepoint(mouse_pos):
                self._open_stop_game_window()
        
        # 如果是电脑出牌事件
        elif event.type == self.ai_act_event:
            if self.can_play_card:
                card = self.ai_player[self.current_player].get_card_to_play()
                self._play_card(card)
            else:
                card = self.ai_player[self.current_player].get_card_to_discard()
                self._discard_card(card)
    
    def _check_events_in_testing_game(self, event: Event):
        # 如果左键点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            mouse_pos = pygame.mouse.get_pos()
            if self.focused_card:
                self._on_focused_card_clicked()
    
    def _check_events_in_game_over_menu(self, event: Event):
        # 如果左键点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            mouse_pos = pygame.mouse.get_pos()
            if self.game_over_menu.rect.collidepoint(mouse_pos):
                mouse_pos = (
                        mouse_pos[0] - self.game_over_menu.rect.left,
                        mouse_pos[1] - self.game_over_menu.rect.top
                    )
                if self.game_over_menu.replay_button.rect.collidepoint(mouse_pos):
                    self.new_game()
                elif self.game_over_menu.exit_button.rect.collidepoint(mouse_pos):
                    self.exit_confirm()
    
    def _open_stop_game_window(self):
        """打开游戏暂停窗口"""
        self._stop_game()
        self.windows.append(StopGameWindow())
        

    def open_rule(self):
        """打开游戏规则界面"""
        self.game_stage = GameStage.rule
        rule_window = RuleWindow()
        self.windows.append(rule_window)
    
    def _stop_game(self):
        if self.game_stage == GameStage.playing:
            pygame.time.set_timer(self.ai_act_event, 0, loops=3)
    
    def _continue_game(self):
        if self.game_stage == GameStage.playing:
            if self.current_player != 0:
                pygame.time.set_timer(self.ai_act_event, self.settings.ai_act_interval, loops=4 - self.current_player)
    
    def exit_confirm(self):
        """确认退出"""
        self.windows.append(ExitWindow())
        self._stop_game()
    
    def _next_turn(self):
        """即将进入下一个玩家的回合"""
        self.end_turn = False
        # 判断是否游戏结束
        # 如果所有玩家均没有手牌了则游戏结束
        if not any(self.hand):
            self._end_game()
            return

        # 玩家打出牌后开始计时，每过一秒电脑行动一次
        if self.current_player == 0:
            pygame.time.set_timer(self.ai_act_event, self.settings.ai_act_interval, loops=3)
        
        # 更新当前玩家 和 当前玩家是否可出牌的状态
        self.current_player = (self.current_player + 1) % 4
        self.can_play_card = False
        for card in self.hand[self.current_player]:
            if card.info in self.playable_cards:
                self.can_play_card = True
                break
    
    def _end_game(self):
        """游戏结束时的结算"""
        # 如果还在计时，则停止计时
        pygame.time.set_timer(self.ai_act_event, 0)
        
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
            self.score[pair[0]] += self.settings.base_score[i] * score_multiply_power
        
        self.game_stage = GameStage.game_over_menu
        self.game_over_menu = GameOverMenu(self, sorted_player_points_pairs, score_multiply_power)
        
        if sorted_player_points_pairs[0][0] == 0:
            if score_multiply_power == 1:
                self.game_over_menu.win_sound.play()
            elif score_multiply_power == 2:
                self.game_over_menu.datong_sound.play()
        else:
            self.game_over_menu.lose_sound.play()
    
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
        card.to_visible()
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
        card.playable = False
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

        for hand in self.hand:
            for hand_card in hand:
                if hand_card.info in self.playable_cards:
                    hand_card.playable = True
        
        self.end_turn = True
        
        # 埋个彩蛋
        if card.info == (1, 13) and self.current_player == 0 and random() < 0.2 and not self.discovered:
            self._stop_game()
            extra_sound1 = Sound('music/cards/梅花13.mp3')
            extra_sound1.play()
            pygame.time.wait(3000)
            extra_sound2 = Sound('music/cards/梅花567.mp3')
            extra_sound2.play(fade_ms=2000)
            pygame.time.wait(10000)
            extra_sound2.fadeout(2000)
            pygame.time.wait(2000)
            extra_sound3 = Sound('music/彩蛋.mp3')
            extra_sound3.play()
            pygame.time.wait(1000)
            self._continue_game()
            self.discovered = True
            return
        
        card.sound.play()
    
    def _discard_card(self, card: Card):
        """当前玩家弃置指定的卡牌"""
        self.discard_sound.play()
        # 将此牌从手中移动到弃牌堆
        self.trashed_cards[self.current_player].add(card)
        self.hand[self.current_player].remove(card)
        
        # 改变被弃牌的UI
        card.to_discard_UI()
        
        self.end_turn = True
            

    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
        self.screen.fill(self.settings.bg_color)
        if self.game_stage == GameStage.start_menu:
            self.start_menu.blitme()
        elif self.game_stage == GameStage.rule:
            pass
        elif self.game_stage == GameStage.playing:
            self.board.blitme()
            self.stop_button.blitme()
            self._draw_cards()
        elif self.game_stage == GameStage.testing:
            self.board.blitme()
            self._draw_cards()
        elif self.game_stage == GameStage.game_over_menu:
            self.board.blitme()
            self._draw_cards()
            # 将牌桌作为背景变暗，以凸显游戏结束界面
            darken(self.screen)
            # 背景变暗后再绘制游戏结束界面
            self.game_over_menu.blitme()
            
        # 如果有窗口需要显示
        if self.windows:
            for covered in self.windows[:-1]:
                covered.blitme()
            darken(self.screen)
            self.windows[-1].blitme()
            
        pygame.display.flip()
    
    def _update_cards(self):
        """更新所有卡牌的图像"""
        
        #  设置我的手牌位置
        left_margin = (self.settings.screen_width
                       - (len(self.hand[0])+len(self.trashed_cards[0])-1) * self.settings.card.hand_xspacing
                       - self.settings.card.width) // 2
        for i, card in enumerate(self.hand[0].sprites() + self.trashed_cards[0].sprites()):
            card.rect.left = left_margin + i * self.settings.card.hand_xspacing
            card.rect.bottom = self.settings.screen_height + 0.6 * self.settings.card.height
        
        # 设置右侧玩家手牌位置
        top_margin = (self.settings.screen_height
                       - (len(self.hand[1])+len(self.trashed_cards[1])-1) * self.settings.card.hand_yspacing
                       - self.settings.card.height) // 2
        for i, card in enumerate(self.hand[1].sprites() + self.trashed_cards[1].sprites()):
            card.rect.top = top_margin + i * self.settings.card.hand_yspacing
            card.rect.right = self.settings.screen_width + 0.6 * self.settings.card.width
        
        # 设置对侧玩家的手牌位置
        right_margin = (self.settings.screen_width
                       - (len(self.hand[2])+len(self.trashed_cards[2])-1) * self.settings.card.hand_xspacing
                       - self.settings.card.width) // 2
        for i, card in enumerate(self.hand[2].sprites() + self.trashed_cards[2].sprites()):
            card.rect.right = self.settings.screen_width - (right_margin + i * self.settings.card.hand_xspacing)
            card.rect.top = 0 - 0.6 * self.settings.card.height
        
        # 设置左侧玩家手牌位置
        top_margin = (self.settings.screen_height
                       - (len(self.hand[3])+len(self.trashed_cards[3])-1) * self.settings.card.hand_yspacing
                       - self.settings.card.height) // 2
        for i, card in enumerate(self.hand[3].sprites() + self.trashed_cards[3].sprites()):
            card.rect.top = top_margin + i * self.settings.card.hand_yspacing
            card.rect.left = 0 - 0.6 * self.settings.card.width
        
        # 设置场上卡牌位置
        for i in range(4):
            for j, card in enumerate(reversed(self.played_cards_greater_7[i])):
                card.rect.centerx = self.settings.field.left_margin + i * self.settings.field.xspacing
                n = len(self.played_cards_greater_7[i])
                card.rect.centery = self.settings.screen_height // 2 - (n-j) * self.settings.field.yspacing

        for i in range(4):
            for j, card in enumerate(self.played_cards_7[i]):
                card.rect.centerx = self.settings.field.left_margin + i * self.settings.field.xspacing
                card.rect.centery = self.settings.screen_height // 2
        
        for i in range(4):
            for j, card in enumerate(self.played_cards_less_7[i]):
                card.rect.centerx = self.settings.field.left_margin + i * self.settings.field.xspacing
                card.rect.centery = self.settings.screen_height // 2 + (j+1) * self.settings.field.yspacing
        
        # 检测鼠标是否聚焦手牌
        self.focused_card = None
        pos = pygame.mouse.get_pos()
        for i, hand in enumerate(self.hand):
            for card in reversed(hand.sprites()):
                # 检测鼠标是否聚焦手牌
                if not self.focused_card and card.rect.collidepoint(pos):
                    self.focused_card = card
                    card.focused = True
                    if i == 0:
                        card.rect.bottom = self.settings.screen_height
                    elif i == 1:
                        card.rect.right = self.settings.screen_width
                    elif i == 2:
                        card.rect.top = 0
                    elif i == 3:
                        card.rect.left = 0
                    else:
                        raise Exception("Too many hand!")
                else:
                    card.focused = False
                
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
                card.blitme()
        
        # 显示弃牌堆
        for player_trashed_cards in self.trashed_cards:
            player_trashed_cards.draw(self.screen)


if __name__ == '__main__':
    game = DaTongSolitaire()
    game.run_game()