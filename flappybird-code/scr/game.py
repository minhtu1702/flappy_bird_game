import pygame
import random
import os
from bird import Bird
from pipe import Pipe
from ground import Ground
from particle import Particle
from powerup import PowerUp

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 30)
        self.large_font = pygame.font.SysFont("Arial", 50)
        self.small_font = pygame.font.SysFont("Arial", 20)

        # trạng thái game
        self.state = "MENU"  # MENU, PLAYING, GAME_OVER

        # load assets
        self.bg_day = pygame.image.load("../assets/images/banngay.png").convert()
        self.bg_evening = pygame.image.load("../assets/images/bandem.png").convert()
        self.bg_night = pygame.image.load("../assets/images/bandem.png").convert()

        self.bg_day = pygame.transform.scale(self.bg_day, (self.width, self.height))
        self.bg_evening = pygame.transform.scale(self.bg_evening, (self.width, self.height))
        self.bg_night = pygame.transform.scale(self.bg_night, (self.width, self.height))

        # Smooth cycling backgrounds (crossfade)
        self.bg_list = [self.bg_day, self.bg_evening, self.bg_night]
        self.bg_current = 0
        self.bg_next = 1 if len(self.bg_list) > 1 else 0
        self.bg_transition_progress = 0.0  # 0.0..1.0
        # How much progress increases per frame (tweak for speed of crossfade)
        self.bg_transition_speed = 0.015
        # Nếu true => đang trong quá trình chuyển nền (crossfade)
        self.bg_transition_active = False
        # Bộ đếm thời gian bay liên tục (tính theo frame)
        self.flight_timer_frames = 0
        # Ngưỡng thời gian (giây) để kích hoạt đổi ngày/đêm luân phiên
        self.bg_time_threshold_seconds = 25
        # Giả định ~60 FPS; chuyển sang frame tương ứng (có thể điều chỉnh)
        self.bg_time_threshold_frames = int(self.bg_time_threshold_seconds * 60)

        # load số cho điểm
        self.numbers = []
        for i in range(10):
            img = pygame.image.load(f"../assets/images/{i}.png").convert_alpha()
            self.numbers.append(img)

        # load âm thanh
        pygame.mixer.init()
        self.sounds = {
            'wing': pygame.mixer.Sound("../assets/sound/wing.wav"),
            'point': pygame.mixer.Sound("../assets/sound/point.wav"),
            'hit': pygame.mixer.Sound("../assets/sound/hit.wav"),
            'die': pygame.mixer.Sound("../assets/sound/die.wav"),
            'swoosh': pygame.mixer.Sound("../assets/sound/swoosh.wav")
        }

        # high score
        self.high_score = self.load_high_score()

        # ⭐ KHAI BÁO bird_types MỘT LẦN DUY NHẤT
        # Đặt mục đầu tiên là chim mặc định (sử dụng bộ ảnh animated red bird)
        self.bird_types = [
            "red",  # special key -> use default animated bird
            "../assets/images/xanhla.png",
            "../assets/images/vang.png",
            "../assets/images/mu3.png",
            "../assets/images/trang.png",
            "../assets/images/tim.png"
        ]

        # ⭐ Tên hiển thị cho từng loại chim
        self.bird_names = [
            "Red Bird",
            "Green Bird",
            "Yellow Bird", 
            "Hat Bird",
            "White Bird",
            "Purple Bird"
        ]

        self.selected_bird = 0

        # ⭐ LOAD bird preview images MỘT LẦN DUY NHẤT
        self.bird_previews = []
        print("\n=== Loading Bird Previews ===")
        for i, bird_path in enumerate(self.bird_types):
            try:
                # Nếu là key đặc biệt (ví dụ "red"), tạo preview từ ảnh default
                if not (isinstance(bird_path, str) and bird_path.endswith('.png')):
                    # load the default mid flap and tint if possible
                    base = pygame.image.load("../assets/images/redbird-midflap.png").convert_alpha()
                    # simple tint map for known keys
                    tint_map = {
                        "red": (255, 0, 0),
                    }
                    tint = tint_map.get(bird_path, None)
                    if tint is not None:
                        img = base.copy()
                        img.fill(tint, special_flags=pygame.BLEND_MULT)
                        preview_img = img
                    else:
                        preview_img = base
                else:
                    # Load ảnh gốc
                    preview_img = pygame.image.load(bird_path).convert_alpha()
                print(f"✓ [{i}] Loaded: {bird_path}")
                print(f"    Original size: {preview_img.get_size()}")
                
                # Scale lên để dễ nhìn
                original_w, original_h = preview_img.get_size()
                scale_factor = 3
                new_w = original_w * scale_factor
                new_h = original_h * scale_factor
                preview_scaled = pygame.transform.scale(preview_img, (new_w, new_h))
                print(f"    Scaled to: {preview_scaled.get_size()}")
                
                self.bird_previews.append(preview_scaled)
                
            except Exception as e:
                print(f"✗ [{i}] Error loading: {bird_path}")
                print(f"    Error: {e}")
                print(f"    Current dir: {os.getcwd()}")
                print(f"    Full path: {os.path.abspath(bird_path)}")
                
                # Tạo placeholder màu sắc nếu không load được
                placeholder = pygame.Surface((102, 72))
                placeholder.fill((100, 100, 100))  # Background xám
                pygame.draw.rect(placeholder, (255, 0, 0), placeholder.get_rect(), 3)  # Viền đỏ
                # Vẽ chữ X
                pygame.draw.line(placeholder, (255, 0, 0), (10, 10), (92, 62), 3)
                pygame.draw.line(placeholder, (255, 0, 0), (92, 10), (10, 62), 3)
                self.bird_previews.append(placeholder)
        
        print(f"\nTotal previews loaded: {len(self.bird_previews)}")
        print("=" * 30 + "\n")

        # difficulty
        self.difficulties = ["Easy", "Medium", "Hard"]
        self.selected_difficulty = 1  # Medium

        # menu state
        self.menu_option = 0  # 0: start, 1: select bird, 2: difficulty

        self.reset_game()

        # particles
        self.particles = []

        # achievements
        self.achievements = self.load_achievements()
        self.new_achievement = None
        # Game over animation state
        self.game_over_timer = 0
        self.go_title_y = -200
        self.go_title_target_y = 40
        self.go_title_speed = 10
        self.go_anim_done = False
        self.replay_rect = None

    def load_high_score(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except:
            return 0

    def save_high_score(self):
        with open("highscore.txt", "w") as f:
            f.write(str(self.high_score))

    def load_achievements(self):
        try:
            with open("achievements.txt", "r") as f:
                return set(line.strip() for line in f)
        except:
            return set()

    def save_achievements(self):
        with open("achievements.txt", "w") as f:
            for ach in self.achievements:
                f.write(ach + "\n")

    def check_achievements(self):
        if self.score >= 1 and "First Pipe" not in self.achievements:
            self.achievements.add("First Pipe")
            self.new_achievement = "First Pipe"
        if self.score >= 10 and "Score 10" not in self.achievements:
            self.achievements.add("Score 10")
            self.new_achievement = "Score 10"
        if self.score >= 50 and "Score 50" not in self.achievements:
            self.achievements.add("Score 50")
            self.new_achievement = "Score 50"
        self.save_achievements()

    # Lưu ý: chuyển nền giờ được điều khiển theo thời gian bay, không theo điểm.

    def set_difficulty(self):
        if self.selected_difficulty == 0:  # Easy
            self.pipe_speed = 1.8
            self.gravity = 0.35
            self.spawn_spacing = 260
            self.max_vertical_shift = 40
            self.gap_min, self.gap_max = 170, 240
        elif self.selected_difficulty == 1:  # Medium
            self.pipe_speed = 2.8
            self.gravity = 0.45
            self.spawn_spacing = 220
            self.max_vertical_shift = 60
            self.gap_min, self.gap_max = 150, 220
        elif self.selected_difficulty == 2:  # Hard
            self.pipe_speed = 3.8
            self.gravity = 0.55
            self.spawn_spacing = 190
            self.max_vertical_shift = 80
            self.gap_min, self.gap_max = 140, 200
        self.bird.gravity = self.gravity

    def reset_game(self):
        self.bird = Bird(100, 300, self.bird_types[self.selected_bird])
        self.pipes = []
        self.score = 0
        self.ground = Ground(self.height - 100, self.width)
        self.pipe_speed = 2.8
        self.spawn_spacing = 220
        self.max_vertical_shift = 60
        self.gap_min, self.gap_max = 150, 220
        self.last_gap_y = self.height // 2
        self.frame_count = 0
        self.powerups = []
        self.bird_power = None
        self.power_timer = 0
        # reset flight timer khi bắt đầu/trò chơi đặt lại
        self.flight_timer_frames = 0

    def handle_event(self, event):
        if self.state == "MENU":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.menu_option == 0:
                        # Start Game
                        self.state = "PLAYING"
                        self.sounds['swoosh'].play()
                        self.bird = Bird(100, 300, self.bird_types[self.selected_bird])
                        self.set_difficulty()
                    elif self.menu_option == 1:
                        # Setup
                        self.state = "SETUP"
                        self.sounds['swoosh'].play()
                    elif self.menu_option == 2:
                        # Exit game
                        pygame.quit()
                        exit()
                elif event.key == pygame.K_UP:
                    self.menu_option = (self.menu_option - 1) % 3
                    self.sounds['swoosh'].play()
                elif event.key == pygame.K_DOWN:
                    self.menu_option = (self.menu_option + 1) % 3
                    self.sounds['swoosh'].play()

        elif self.state == "SETUP":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.selected_bird = (self.selected_bird - 1) % len(self.bird_types)
                    self.sounds['swoosh'].play()
                elif event.key == pygame.K_RIGHT:
                    self.selected_bird = (self.selected_bird + 1) % len(self.bird_types)
                    self.sounds['swoosh'].play()
                elif event.key == pygame.K_UP:
                    self.selected_difficulty = (self.selected_difficulty - 1) % len(self.difficulties)
                    self.sounds['swoosh'].play()
                elif event.key == pygame.K_DOWN:
                    self.selected_difficulty = (self.selected_difficulty + 1) % len(self.difficulties)
                    self.sounds['swoosh'].play()
                elif event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    # Quay lại menu chính sau khi setup xong
                    self.state = "MENU"
                    self.sounds['swoosh'].play()

        elif self.state == "PLAYING":
            self.bird.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.sounds['wing'].play()
                for _ in range(5):
                    self.particles.append(Particle(self.bird.x, self.bird.y, (255, 255, 0)))

        elif self.state == "GAME_OVER":
            # Keyboard: SPACE to retry, M or ESC to return to menu
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.reset_game()
                    self.state = "PLAYING"
                    self.sounds['swoosh'].play()
                elif event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                    self.state = "MENU"
                    self.reset_game()
            # Mouse: click replay button (if present)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.replay_rect and self.replay_rect.collidepoint(event.pos):
                    self.reset_game()
                    self.state = "PLAYING"
                    self.sounds['swoosh'].play()
                elif getattr(self, 'menu_rect', None) and self.menu_rect.collidepoint(event.pos):
                    self.state = "MENU"
                    self.reset_game()

    def update(self):
        # Nếu đang trong quá trình chuyển nền thì tiến hành tăng tiến độ
        if self.bg_transition_active:
            self.bg_transition_progress += self.bg_transition_speed
            if self.bg_transition_progress >= 1.0:
                # Hoàn tất chuyển tiếp -> cập nhật chỉ số và tắt state
                self.bg_transition_progress = 0.0
                self.bg_current = self.bg_next
                self.bg_transition_active = False
        if self.state == "PLAYING":
            self.bird.update()
            self.frame_count += 1

            # Tăng bộ đếm thời gian bay; nếu đạt ngưỡng thì đổi ngày/đêm luân phiên
            self.flight_timer_frames += 1
            if (self.flight_timer_frames >= self.bg_time_threshold_frames
                    and not self.bg_transition_active):
                # Luân phiên day <-> night (giữa chỉ số 0 và 2 của bg_list)
                if len(self.bg_list) >= 3:
                    if self.bg_current == 0:
                        self.bg_next = 2
                    else:
                        self.bg_next = 0
                else:
                    # fallback: next background tuần tự
                    self.bg_next = (self.bg_current + 1) % len(self.bg_list)
                self.bg_transition_progress = 0.0
                self.bg_transition_active = True
                # reset bộ đếm sau khi khởi động chuyển nền
                self.flight_timer_frames = 0

            # tăng tốc độ theo thời gian
            if self.frame_count % 900 == 0:  # mỗi 15 giây
                self.pipe_speed += 0.3

            for pipe in self.pipes[:]:
                pipe.speed = self.pipe_speed
                pipe.update()
                # score as soon as bird passes the pipe center (more immediate feedback)
                if not getattr(pipe, 'scored', False) and pipe.x + pipe.width < self.bird.x:
                    pipe.scored = True
                    self.score += 1
                    self.sounds['point'].play()
                    # Chỉ kiểm tra achievements; không đổi background theo điểm nữa
                    self.check_achievements()
                # remove pipes when fully off screen
                if pipe.off_screen():
                    self.pipes.remove(pipe)

            # Spawn pipes with smoothed vertical movement so gaps are fair
            if len(self.pipes) == 0 or self.pipes[-1].x < self.width - self.spawn_spacing:
                # choose gap height from difficulty range
                gap_height = random.randint(self.gap_min, self.gap_max)

                # compute allowed vertical bounds for the center of the gap
                top_limit = 80 + gap_height // 2
                bottom_limit = self.ground.y - 80 - gap_height // 2

                # start from previous gap center and shift within max_vertical_shift
                prev = getattr(self, 'last_gap_y', self.height // 2)
                new_center = prev + random.randint(-self.max_vertical_shift, self.max_vertical_shift)
                # clamp
                new_center = max(top_limit, min(bottom_limit, new_center))

                self.pipes.append(Pipe(self.width, new_center, gap_height))
                self.last_gap_y = new_center
                # add powerup randomly
                if random.random() < 0.1:  # 10% chance
                    self.powerups.append(PowerUp(self.width, random.randint(200, 400)))

            # update powerups
            for pu in self.powerups[:]:
                pu.update()
                if pu.off_screen():
                    self.powerups.remove(pu)
                elif pu.rect.colliderect(self.bird.get_rect()):
                    self.powerups.remove(pu)
                    self.bird_power = "speed"
                    self.power_timer = 300  # 5 seconds
                    self.sounds['point'].play()

            # kiểm tra va chạm với pipe
            for pipe in self.pipes:
                if pipe.collides_with(self.bird):
                    self.game_over()

            # kiểm tra va chạm với mặt đất
            if self.bird.y + self.bird.image.get_height() >= self.ground.y:
                self.game_over()

            self.ground.speed = self.pipe_speed
            self.ground.update()

            # update power
            if self.power_timer > 0:
                self.power_timer -= 1
                if self.bird_power == "speed":
                    self.bird.velocity -= 0.1
            else:
                self.bird_power = None

            # update particles
            for p in self.particles[:]:
                p.update()
                if p.is_dead():
                    self.particles.remove(p)

    def game_over(self):
        self.sounds['hit'].play()
        # shorter pause so animation feels snappier
        pygame.time.wait(200)
        self.sounds['die'].play()
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        # enter game over state and initialize animation
        self.state = "GAME_OVER"
        self.game_over_timer = 0
        self.go_title_y = -120
        self.go_title_target_y = 40
        self.go_title_speed = 12
        self.go_anim_done = False
        # default replay rect (will be updated in draw)
        self.replay_rect = pygame.Rect(self.width // 2 - 60, self.height // 2 + 80, 120, 44)

    def draw_score(self, score, x, y):
        score_str = str(score)
        total_width = sum(self.numbers[int(d)].get_width() for d in score_str)
        start_x = x - total_width // 2
        for digit in score_str:
            img = self.numbers[int(digit)]
            self.screen.blit(img, (start_x, y))
            start_x += img.get_width()

    def draw(self):
        # Smooth crossfade between backgrounds in `self.bg_list`
        if len(self.bg_list) == 0:
            self.screen.fill((0, 0, 0))
        elif len(self.bg_list) == 1:
            self.screen.blit(self.bg_list[0], (0, 0))
        else:
            # Nếu đang chuyển thì blend giữa current và next, nếu không thì vẽ current
            if self.bg_transition_active:
                progress = max(0.0, min(1.0, self.bg_transition_progress))
                alpha_next = int(progress * 255)
                alpha_cur = 255 - alpha_next

                cur_surf = self.bg_list[self.bg_current].copy()
                next_surf = self.bg_list[self.bg_next].copy()
                cur_surf.set_alpha(alpha_cur)
                next_surf.set_alpha(alpha_next)

                # draw blended
                self.screen.blit(cur_surf, (0, 0))
                self.screen.blit(next_surf, (0, 0))
            else:
                self.screen.blit(self.bg_list[self.bg_current], (0, 0))

        if self.state == "MENU":
            title_text = self.large_font.render("Flappy Bird", True, (255, 255, 255))
            self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 150))

            options = ["Start Game", "Setup", "Exit"]
            for i, opt in enumerate(options):
                color = (255, 255, 0) if i == self.menu_option else (255, 255, 255)
                text = self.font.render(f"{'> ' if i == self.menu_option else '  '}{opt}", True, color)
                self.screen.blit(text, (self.width // 2 - text.get_width() // 2, 250 + i * 50))

        elif self.state == "PLAYING":
            self.bird.draw(self.screen)
            for pipe in self.pipes:
                pipe.draw(self.screen)
            for pu in self.powerups:
                pu.draw(self.screen)
            self.draw_score(self.score, self.width // 2, 50)
            self.ground.draw(self.screen)
            # draw particles
            for p in self.particles:
                p.draw(self.screen)
            # show power
            if self.bird_power:
                power_text = self.font.render(f"Power: {self.bird_power}", True, (0, 255, 0))
                self.screen.blit(power_text, (10, 80))
            # show new achievement
            if self.new_achievement:
                ach_text = self.font.render(f"Achievement: {self.new_achievement}!", True, (255, 215, 0))
                self.screen.blit(ach_text, (self.width // 2 - ach_text.get_width() // 2, 100))
                # reset after a few frames
                if self.frame_count % 120 == 0:  # 2 seconds
                    self.new_achievement = None

        elif self.state == "GAME_OVER":
            # Dark translucent overlay
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            # Animate title dropping (like original)
            if not getattr(self, 'go_anim_done', False):
                self.go_title_y += self.go_title_speed
                if self.go_title_y >= self.go_title_target_y:
                    self.go_title_y = self.go_title_target_y
                    self.go_anim_done = True

            title_text = self.large_font.render("Game Over", True, (255, 255, 255))
            shadow = self.large_font.render("Game Over", True, (0, 0, 0))
            tx = self.width // 2 - title_text.get_width() // 2
            self.screen.blit(shadow, (tx + 3, self.go_title_y + 3))
            self.screen.blit(title_text, (tx, self.go_title_y))

            # Score panel (compact, like original)
            panel_w, panel_h = 320, 140
            panel_x = self.width // 2 - panel_w // 2
            panel_y = self.go_title_y + 80
            panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
            pygame.draw.rect(self.screen, (246, 246, 246), panel_rect, border_radius=8)
            pygame.draw.rect(self.screen, (190, 190, 190), panel_rect, 2, border_radius=8)

            # Medal
            medal_center = (panel_x + 56, panel_y + panel_h // 2)
            if self.score >= 20:
                medal_color = (212, 175, 55)
            elif self.score >= 10:
                medal_color = (192, 192, 192)
            elif self.score >= 5:
                medal_color = (205, 127, 50)
            else:
                medal_color = (150, 150, 150)
            pygame.draw.circle(self.screen, medal_color, medal_center, 30)
            pygame.draw.circle(self.screen, (255, 255, 255), medal_center, 12)

            # Right side: Score and Best using number sprites
            label_font = self.small_font
            lbl_score = label_font.render("SCORE", True, (100, 100, 100))
            lbl_best = label_font.render("BEST", True, (100, 100, 100))
            right_label_x = panel_x + 140
            self.screen.blit(lbl_score, (right_label_x, panel_y + 12))
            self.draw_score(self.score, panel_x + 220, panel_y + 36)
            self.screen.blit(lbl_best, (right_label_x, panel_y + 72))
            self.draw_score(self.high_score, panel_x + 220, panel_y + 96)

            # Buttons below panel: RETRY and MENU
            btn_w, btn_h = 120, 44
            menu_w = 120
            spacing = 12
            total_w = btn_w + menu_w + spacing
            start_x = self.width // 2 - total_w // 2
            btn_y = panel_y + panel_h + 18

            retry_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
            menu_rect = pygame.Rect(start_x + btn_w + spacing, btn_y, menu_w, btn_h)

            pygame.draw.rect(self.screen, (255, 200, 0), retry_rect, border_radius=22)
            pygame.draw.rect(self.screen, (200, 150, 0), retry_rect, 2, border_radius=22)
            retry_txt = self.font.render("RETRY", True, (30, 30, 30))
            self.screen.blit(retry_txt, (retry_rect.x + retry_rect.w // 2 - retry_txt.get_width() // 2, retry_rect.y + retry_rect.h // 2 - retry_txt.get_height() // 2))

            pygame.draw.rect(self.screen, (180, 180, 180), menu_rect, border_radius=22)
            pygame.draw.rect(self.screen, (140, 140, 140), menu_rect, 2, border_radius=22)
            menu_txt = self.font.render("MENU", True, (30, 30, 30))
            self.screen.blit(menu_txt, (menu_rect.x + menu_rect.w // 2 - menu_txt.get_width() // 2, menu_rect.y + menu_rect.h // 2 - menu_txt.get_height() // 2))

            self.replay_rect = retry_rect
            self.menu_rect = menu_rect

            # Hint
            hint = self.small_font.render("Press SPACE or click RETRY", True, (200, 200, 200))
            self.screen.blit(hint, (self.width // 2 - hint.get_width() // 2, btn_y + btn_h + 12))

        elif self.state == "SETUP":
            # ⭐ SETUP SCREEN với BIRD PREVIEW đẹp hơn
            setup_text = self.large_font.render("Setup", True, (255, 255, 255))
            self.screen.blit(setup_text, (self.width // 2 - setup_text.get_width() // 2, 100))

            # ⭐ Vẽ khung cho bird preview
            preview_box_rect = pygame.Rect(self.width // 2 - 130, 170, 260, 160)
            pygame.draw.rect(self.screen, (50, 50, 50), preview_box_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), preview_box_rect, 3)

            # ⭐ Hiển thị tên bird
            bird_name = self.bird_names[self.selected_bird]
            bird_text = self.font.render(bird_name, True, (255, 255, 0))
            self.screen.blit(bird_text, (self.width // 2 - bird_text.get_width() // 2, 180))

            # ⭐ VẼ BIRD PREVIEW Ở GIỮA KHUNG
            if self.selected_bird < len(self.bird_previews):
                preview_img = self.bird_previews[self.selected_bird]
                preview_x = self.width // 2 - preview_img.get_width() // 2
                preview_y = 230
                
                # Vẽ background trắng phía sau để thấy rõ bird
                bg_rect = pygame.Rect(preview_x - 5, preview_y - 5, 
                                     preview_img.get_width() + 10, 
                                     preview_img.get_height() + 10)
                pygame.draw.rect(self.screen, (255, 255, 255), bg_rect)
                
                # Vẽ bird
                self.screen.blit(preview_img, (preview_x, preview_y))
                
                # Vẽ viền xung quanh bird để dễ thấy
                border_rect = pygame.Rect(preview_x - 2, preview_y - 2,
                                         preview_img.get_width() + 4,
                                         preview_img.get_height() + 4)
                pygame.draw.rect(self.screen, (255, 215, 0), border_rect, 2)
            else:
                # Hiển thị thông báo lỗi nếu không có preview
                error_text = self.small_font.render("No preview available", True, (255, 0, 0))
                self.screen.blit(error_text, (self.width // 2 - error_text.get_width() // 2, 250))

            # ⭐ Vẽ mũi tên trái phải
            arrow_y = 260
            left_arrow = self.font.render("◀", True, (255, 255, 255))
            right_arrow = self.font.render("▶", True, (255, 255, 255))
            self.screen.blit(left_arrow, (self.width // 2 - 100, arrow_y))
            self.screen.blit(right_arrow, (self.width // 2 + 80, arrow_y))

            # ⭐ Hiển thị số thứ tự
            bird_num_text = self.small_font.render(f"{self.selected_bird + 1}/{len(self.bird_types)}", True, (200, 200, 200))
            self.screen.blit(bird_num_text, (self.width // 2 - bird_num_text.get_width() // 2, 305))

            # ⭐ Difficulty section
            diff_y_start = 360
            diff_label = self.font.render("Difficulty:", True, (255, 255, 255))
            self.screen.blit(diff_label, (self.width // 2 - diff_label.get_width() // 2, diff_y_start))

            # Vẽ khung difficulty
            diff_box_rect = pygame.Rect(self.width // 2 - 80, diff_y_start + 40, 160, 50)
            pygame.draw.rect(self.screen, (50, 50, 50), diff_box_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), diff_box_rect, 3)

            # Hiển thị difficulty với màu
            diff_colors = {
                0: (0, 255, 0),    # Easy - Green
                1: (255, 255, 0),  # Medium - Yellow
                2: (255, 0, 0)     # Hard - Red
            }
            diff_color = diff_colors.get(self.selected_difficulty, (255, 255, 255))
            diff_text = self.font.render(self.difficulties[self.selected_difficulty], True, diff_color)
            self.screen.blit(diff_text, (self.width // 2 - diff_text.get_width() // 2, diff_y_start + 50))

            # ⭐ Hướng dẫn controls
            hints = [
                "◀ ▶  Change bird",
                "▲ ▼  Change difficulty",
                "SPACE  Back to menu"
            ]

            hint_y_start = 480
            for i, line in enumerate(hints):
                hint_text = self.small_font.render(line, True, (200, 200, 200))
                self.screen.blit(hint_text, (self.width // 2 - hint_text.get_width() // 2, hint_y_start + i * 25))