import pygame
import random
import os
import math
from bird import Bird
from pipe import Pipe
from ground import Ground
from particle import Particle
from powerup import PowerUp
from utils import ResourceManager, FileManager

class Game:
    def __init__(self, screen, resource_manager=None, file_manager=None):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 30)
        self.large_font = pygame.font.SysFont("Arial", 50)
        self.small_font = pygame.font.SysFont("Arial", 20)

        # trạng thái game
        self.state = "MENU"  # MENU, PLAYING, GAME_OVER

        # resource/file managers
        self.resource_manager = resource_manager if resource_manager is not None else ResourceManager()
        self.file_manager = file_manager if file_manager is not None else FileManager()

        # load assets via ResourceManager
        self.bg_day = self.resource_manager.load_image("../assets/images/banngay.png").convert()
        self.bg_evening = self.resource_manager.load_image("../assets/images/bandem.png").convert()
        self.bg_night = self.resource_manager.load_image("../assets/images/bandem.png").convert()

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
        # background horizontal offsets for subtle motion
        self.bg_offsets = [0.0 for _ in self.bg_list]
        # scroll speeds (pixels per frame) for day, evening, night
        self.bg_scroll_speeds = [0.35, 0.12, 0.04][:len(self.bg_list)]

        # starfield for night background (drawn on top)
        self.stars = []
        if len(self.bg_list) >= 3:
            for _ in range(80):
                sx = random.randint(0, self.width)
                sy = random.randint(0, max(1, self.height // 2))
                ssize = random.randint(1, 3)
                phase = random.random() * 2 * math.pi
                spd = random.uniform(0.02, 0.5)
                alpha_base = random.randint(120, 220)
                self.stars.append({
                    'x': sx, 'y': sy, 'size': ssize, 'phase': phase, 'speed': spd, 'alpha_base': alpha_base
                })
        # Bộ đếm thời gian bay liên tục (tính theo frame)
        self.flight_timer_frames = 0
        # Ngưỡng thời gian (giây) để kích hoạt đổi ngày/đêm luân phiên
        self.bg_time_threshold_seconds = 20
        # Giả định ~60 FPS; chuyển sang frame tương ứng (có thể điều chỉnh)
        self.bg_time_threshold_frames = int(self.bg_time_threshold_seconds * 60)

        # load số cho điểm
        self.numbers = []
        for i in range(10):
            img = self.resource_manager.load_image(f"../assets/images/{i}.png").convert_alpha()
            self.numbers.append(img)

        # load sounds via ResourceManager
        pygame.mixer.init()
        self.sounds = {
            'wing': self.resource_manager.load_sound("wing.wav"),
            'point': self.resource_manager.load_sound("point.wav"),
            'hit': self.resource_manager.load_sound("hit.wav"),
            'die': self.resource_manager.load_sound("die.wav"),
            'swoosh': self.resource_manager.load_sound("swoosh.wav")
        }

        # high score
        self.high_score = self.load_high_score()

        # ⭐ KHAI BÁO bird_types MỘT LẦN DUY NHẤT
        # Each bird is defined as a list of its animation frame file paths.
        self.bird_types = [
            [
                "../assets/images/chim do 1.png",
                "../assets/images/chim do 2.png",
                "../assets/images/chim do 3.png",
            ],
            [
                "../assets/images/chim den 1.png",
                "../assets/images/chim den 2.png",
                "../assets/images/chim den 3.png",
            ],
            [
                "../assets/images/chim xanh nước 1.png",
                "../assets/images/chim xanh nước 2.png",
                "../assets/images/chim xanh nước 3.png",
            ],
            [
                "../assets/images/chim tim 1.png",
                "../assets/images/chim tim 2.png",
                "../assets/images/chim tim 3.png",
            ],
            [
                "../assets/images/chim trang 1.png",
                "../assets/images/chim trang 2.png",
                "../assets/images/chim trang 3.png",
            ],
            [
                "../assets/images/chim vang 1.png",
                "../assets/images/chim vang 2.png",
                "../assets/images/chim vang 3.png",
            ],
            [
                "../assets/images/chim xanh lá 1.png",
                "../assets/images/chim xanh lá 2.png",
                "../assets/images/chim xanh lá 3.png",
            ]
        ]

        # ⭐ Tên hiển thị cho từng loại chim (theo thứ tự trên)
        self.bird_names = [
            "Chim Đỏ",
            "Chim Đen",
            "Chim Xanh Nước",
            "Chim Tím",
            "Chim Trắng",
            "Chim Vàng",
            "Chim Xanh Lá"
        ]

        self.selected_bird = 0

        # ⭐ LOAD bird preview images MỘT LẦN DUY NHẤT
        self.bird_previews = []
        print("\n=== Loading Bird Previews ===")
        for i, bird_path in enumerate(self.bird_types):
            try:
                # Handle multiple types: list of files, directory, single png, or special key
                if isinstance(bird_path, (list, tuple)):
                    # use first image in list as preview
                    if self.resource_manager:
                        preview_img = self.resource_manager.load_image(bird_path[0]).convert_alpha()
                    else:
                        preview_img = pygame.image.load(bird_path[0]).convert_alpha()
                elif isinstance(bird_path, str) and os.path.isdir(bird_path):
                    files = sorted([f for f in os.listdir(bird_path) if f.lower().endswith('.png')])
                    if files:
                        if self.resource_manager:
                            preview_img = self.resource_manager.load_image(os.path.join(bird_path, files[0])).convert_alpha()
                        else:
                            preview_img = pygame.image.load(os.path.join(bird_path, files[0])).convert_alpha()
                    else:
                        raise FileNotFoundError(f"No pngs in directory {bird_path}")
                elif isinstance(bird_path, str) and bird_path.endswith('.png'):
                    # Load single image
                    if self.resource_manager:
                        preview_img = self.resource_manager.load_image(bird_path).convert_alpha()
                    else:
                        preview_img = pygame.image.load(bird_path).convert_alpha()
                else:
                    # special key (e.g. "red") -> create preview from default redbird
                    if self.resource_manager:
                        base = self.resource_manager.load_image("../assets/images/redbird-midflap.png").convert_alpha()
                    else:
                        base = pygame.image.load("../assets/images/redbird-midflap.png").convert_alpha()
                    tint_map = {"red": (255, 0, 0)}
                    tint = tint_map.get(bird_path, None)
                    if tint is not None:
                        img = base.copy()
                        img.fill(tint, special_flags=pygame.BLEND_MULT)
                        preview_img = img
                    else:
                        preview_img = base
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
        return self.file_manager.read_high_score()

    def save_high_score(self):
        self.file_manager.write_high_score(self.high_score)

    def load_achievements(self):
        return self.file_manager.read_achievements()

    def save_achievements(self):
        self.file_manager.write_achievements(self.achievements)

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

    # Lưu ý: chuyển nền được điều khiển theo thời gian bay, không theo điểm.

    def set_difficulty(self):
        if self.selected_difficulty == 0:  # Easy
            self.pipe_speed = 1.8
            self.gravity = 0.35
            # slightly increase spacing so Easy feels more relaxed
            self.spawn_spacing = 290
            self.max_vertical_shift = 40
            # Reduce gap size (easier still than others but smaller than before)
            self.gap_min, self.gap_max = 150, 200
        elif self.selected_difficulty == 1:  # Medium
            self.pipe_speed = 2.8
            self.gravity = 0.45
            # increase spacing a bit for Medium
            self.spawn_spacing = 250
            self.max_vertical_shift = 60
            # Reduce gap size for Medium to increase difficulty
            self.gap_min, self.gap_max = 130, 180
        elif self.selected_difficulty == 2:  # Hard
            self.pipe_speed = 3.8
            self.gravity = 0.55
            # increase spacing slightly for Hard to be fair
            self.spawn_spacing = 220
            self.max_vertical_shift = 80
            # Reduce gap size for Hard to make it more challenging
            self.gap_min, self.gap_max = 120, 160
        self.bird.gravity = self.gravity

    def reset_game(self):
        self.bird = Bird(100, 300, self.bird_types[self.selected_bird], resource_manager=self.resource_manager)
        self.pipes = []
        self.score = 0
        self.ground = Ground(self.height - 100, self.width, resource_manager=self.resource_manager)
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
        # pipe spawn pattern state to make gaps less predictable
        self.pipe_pattern = None
        self.pipe_pattern_count = 0
        self.pipe_zig_dir = 1

    def handle_event(self, event):
        if self.state == "MENU":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.menu_option == 0:
                        # Start Game
                        self.state = "PLAYING"
                        self.sounds['swoosh'].play()
                        self.bird = Bird(100, 300, self.bird_types[self.selected_bird], resource_manager=self.resource_manager)
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
            # Mouse click on arrow buttons
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if getattr(self, 'left_btn_rect', None) and self.left_btn_rect.collidepoint((mx, my)):
                    self.selected_bird = (self.selected_bird - 1) % len(self.bird_types)
                    self.sounds['swoosh'].play()
                elif getattr(self, 'right_btn_rect', None) and self.right_btn_rect.collidepoint((mx, my)):
                    self.selected_bird = (self.selected_bird + 1) % len(self.bird_types)
                    self.sounds['swoosh'].play()
                # also allow clicks on the hint buttons below
                elif getattr(self, 'hint_left_rect', None) and self.hint_left_rect.collidepoint((mx, my)):
                    self.selected_bird = (self.selected_bird - 1) % len(self.bird_types)
                    self.sounds['swoosh'].play()
                elif getattr(self, 'hint_right_rect', None) and self.hint_right_rect.collidepoint((mx, my)):
                    self.selected_bird = (self.selected_bird + 1) % len(self.bird_types)
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
        # update subtle background scrolling offsets and starfield
        for i in range(len(self.bg_offsets)):
            self.bg_offsets[i] = (self.bg_offsets[i] + self.bg_scroll_speeds[i]) % max(1, self.width)
        if self.stars:
            for s in self.stars:
                s['x'] -= s['speed']
                if s['x'] < 0:
                    s['x'] += self.width
                s['phase'] += 0.04
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

                # previous gap center
                prev = getattr(self, 'last_gap_y', self.height // 2)

                # Choose or continue a pipe pattern to make vertical placement harder to predict
                if not getattr(self, 'pipe_pattern', None) or self.pipe_pattern_count <= 0:
                    r = random.random()
                    if r < 0.40:
                        self.pipe_pattern = 'random'
                        self.pipe_pattern_count = random.randint(1, 3)
                    elif r < 0.70:
                        self.pipe_pattern = 'smooth'
                        self.pipe_pattern_count = random.randint(2, 5)
                    else:
                        self.pipe_pattern = 'zigzag'
                        self.pipe_pattern_count = random.randint(3, 6)
                        self.pipe_zig_dir = random.choice([-1, 1])

                if self.pipe_pattern == 'random':
                    # anywhere in bounds
                    new_center = random.randint(top_limit, bottom_limit)

                elif self.pipe_pattern == 'zigzag':
                    # alternate moving up/down by a larger step to force unpredictability
                    step = max(20, self.max_vertical_shift)
                    new_center = prev + self.pipe_zig_dir * step
                    # flip direction occasionally
                    if random.random() < 0.4:
                        self.pipe_zig_dir *= -1

                else:  # smooth
                    # mostly small shifts with occasional jitter
                    shift = random.randint(-max(6, self.max_vertical_shift // 2), max(6, self.max_vertical_shift // 2))
                    jitter = random.randint(-5, 5)
                    new_center = prev + shift + jitter

                # clamp into allowed range
                new_center = max(top_limit, min(bottom_limit, new_center))

                self.pipes.append(Pipe(self.width, new_center, gap_height, resource_manager=self.resource_manager))
                # ensure pipes use resource manager for images
                self.pipes[-1].image_bottom = self.pipes[-1].image_bottom
                self.last_gap_y = new_center
                self.pipe_pattern_count -= 1
                # add powerup randomly
                if random.random() < 0.1:  # 10% chance
                    self.powerups.append(PowerUp(self.width, random.randint(200, 400), resource_manager=self.resource_manager))

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

                # For transitioning, draw both backgrounds with their own offsets
                cur_idx = self.bg_current
                next_idx = self.bg_next

                cur_surf = self.bg_list[cur_idx].copy()
                next_surf = self.bg_list[next_idx].copy()

                # apply scrolling offsets for each
                cur_off = int(self.bg_offsets[cur_idx])
                next_off = int(self.bg_offsets[next_idx])

                cur_surf.set_alpha(alpha_cur)
                next_surf.set_alpha(alpha_next)

                # draw tiled with offsets
                self.screen.blit(cur_surf, (-cur_off, 0))
                self.screen.blit(cur_surf, (self.width - cur_off, 0))
                self.screen.blit(next_surf, (-next_off, 0))
                self.screen.blit(next_surf, (self.width - next_off, 0))
            else:
                # draw scrolling background (tile horizontally for continuous motion)
                cur_idx = self.bg_current
                cur_surf = self.bg_list[cur_idx]
                offset = int(self.bg_offsets[cur_idx])
                self.screen.blit(cur_surf, (-offset, 0))
                self.screen.blit(cur_surf, (self.width - offset, 0))

        if self.state == "MENU":
            # animated title bob for liveliness
            bob = int(math.sin(pygame.time.get_ticks() / 600.0) * 6)
            title_y = 140 + bob
            shadow = self.large_font.render("Flappy Bird", True, (0, 0, 0))
            title_text = self.large_font.render("Flappy Bird", True, (255, 255, 255))
            tx = self.width // 2 - title_text.get_width() // 2
            self.screen.blit(shadow, (tx + 4, title_y + 4))
            self.screen.blit(title_text, (tx, title_y))

            # translucent panel behind options
            panel_w, panel_h = 320, 220
            panel_x = self.width // 2 - panel_w // 2
            panel_y = title_y + 70
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((10, 10, 10, 140))
            self.screen.blit(panel, (panel_x, panel_y))

            # options as rounded buttons
            options = ["Start Game", "Setup", "Exit"]
            btn_w, btn_h = 220, 44
            spacing = 14
            for i, opt in enumerate(options):
                btn_x = self.width // 2 - btn_w // 2
                btn_y = panel_y + 20 + i * (btn_h + spacing)
                rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                if i == self.menu_option:
                    pygame.draw.rect(self.screen, (255, 200, 0), rect, border_radius=22)
                    pygame.draw.rect(self.screen, (200, 150, 0), rect, 3, border_radius=22)
                    text = self.font.render(opt, True, (30, 30, 30))
                else:
                    pygame.draw.rect(self.screen, (80, 80, 80), rect, border_radius=22)
                    pygame.draw.rect(self.screen, (120, 120, 120), rect, 2, border_radius=22)
                    text = self.font.render(opt, True, (230, 230, 230))
                self.screen.blit(text, (rect.x + rect.w // 2 - text.get_width() // 2, rect.y + rect.h // 2 - text.get_height() // 2))

            # show small bird preview next to the panel (for Setup preview/visual polish)
            try:
                preview = self.bird_previews[self.selected_bird]
                pv_w, pv_h = preview.get_size()
                scale = 0.8
                sw, sh = int(pv_w * scale), int(pv_h * scale)
                preview_s = pygame.transform.smoothscale(preview, (sw, sh))
                pv_x = panel_x - sw - 20
                pv_y = panel_y + panel_h // 2 - sh // 2
                # white frame behind
                pygame.draw.rect(self.screen, (255, 255, 255), (pv_x - 6, pv_y - 6, sw + 12, sh + 12), border_radius=8)
                self.screen.blit(preview_s, (pv_x, pv_y))
            except Exception:
                pass

        # If night background is active, draw starfield on top for twinkle/motion
        # Draw whenever night is current OR next during a transition to make it smooth
        night_indices = []
        if len(self.bg_list) >= 3:
            night_indices.append(2)
        draw_stars = False
        if self.bg_transition_active:
            if self.bg_current in night_indices or self.bg_next in night_indices:
                draw_stars = True
        else:
            if self.bg_current in night_indices:
                draw_stars = True

        if draw_stars and self.stars:
            star_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            for s in self.stars:
                a = int(max(10, min(255, s['alpha_base'] + math.sin(s['phase']) * 60)))
                col = (255, 255, 255, a)
                pygame.draw.circle(star_surf, col, (int(s['x']), int(s['y'])), s['size'])
            self.screen.blit(star_surf, (0, 0))

        if self.state == "PLAYING":
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


            # ⭐ VẼ nút mũi tên trái/phải giống style của hint buttons (đồng bộ)
            arrow_y = 260
            btn_w, btn_h = 36, 36
            left_btn_rect = pygame.Rect(self.width // 2 - 100 - btn_w // 2, arrow_y - 8, btn_w, btn_h)
            right_btn_rect = pygame.Rect(self.width // 2 + 80 - btn_w // 2, arrow_y - 8, btn_w, btn_h)

            # Nền và viền tương đồng với hint (darker bg + white border)
            pygame.draw.rect(self.screen, (50, 50, 50), left_btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), left_btn_rect, 2, border_radius=6)
            pygame.draw.rect(self.screen, (50, 50, 50), right_btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), right_btn_rect, 2, border_radius=6)

            # Vẽ ký hiệu mũi tên ở giữa nút (dùng polygon để đảm bảo hiển thị)
            arrow_color = (255, 255, 255)
            # left triangle
            cx = left_btn_rect.x + left_btn_rect.w // 2
            cy = left_btn_rect.y + left_btn_rect.h // 2
            s = min(left_btn_rect.w, left_btn_rect.h) // 3
            left_tri = [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)]
            pygame.draw.polygon(self.screen, arrow_color, left_tri)
            # right triangle
            cx = right_btn_rect.x + right_btn_rect.w // 2
            cy = right_btn_rect.y + right_btn_rect.h // 2
            s = min(right_btn_rect.w, right_btn_rect.h) // 3
            right_tri = [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
            pygame.draw.polygon(self.screen, arrow_color, right_tri)
            # Lưu rect để xử lý click
            self.left_btn_rect = left_btn_rect
            self.right_btn_rect = right_btn_rect

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

            # ⭐ Hướng dẫn controls (thay dòng đổi chim bằng nút tương tác)
            hint_y_start = 480

            # Draw small hint buttons for Change Bird (centered)
            hint_btn_w, hint_btn_h = 36, 36
            gap = 8
            total_w = hint_btn_w * 2 + gap + 120  # two arrows + label width approx
            start_x = self.width // 2 - total_w // 2

            hint_left = pygame.Rect(start_x, hint_y_start, hint_btn_w, hint_btn_h)
            hint_label_x = hint_left.x + hint_btn_w + gap
            hint_label = self.small_font.render("Change bird", True, (200, 200, 200))
            hint_right = pygame.Rect(hint_label_x + hint_label.get_width() + gap, hint_y_start, hint_btn_w, hint_btn_h)

            pygame.draw.rect(self.screen, (50, 50, 50), hint_left, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), hint_left, 2, border_radius=6)
            pygame.draw.rect(self.screen, (50, 50, 50), hint_right, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), hint_right, 2, border_radius=6)

            # draw triangle arrows for hint buttons to avoid font glyph issues
            arrow_color = (255, 255, 255)
            # left small triangle
            cx = hint_left.x + hint_left.w // 2
            cy = hint_left.y + hint_left.h // 2
            s = min(hint_left.w, hint_left.h) // 3
            left_tri = [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)]
            pygame.draw.polygon(self.screen, arrow_color, left_tri)
            # label
            self.screen.blit(hint_label, (hint_label_x, hint_y_start + hint_btn_h//2 - hint_label.get_height()//2))
            # right small triangle
            cx = hint_right.x + hint_right.w // 2
            cy = hint_right.y + hint_right.h // 2
            s = min(hint_right.w, hint_right.h) // 3
            right_tri = [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
            pygame.draw.polygon(self.screen, arrow_color, right_tri)

            # save hint rects to allow clicking these too
            self.hint_left_rect = hint_left
            self.hint_right_rect = hint_right

            # remaining textual hints
            other_hints = [
                "▲ ▼  Change difficulty",
                "SPACE  Back to menu"
            ]
            for i, line in enumerate(other_hints):
                hint_text = self.small_font.render(line, True, (200, 200, 200))
                self.screen.blit(hint_text, (self.width // 2 - hint_text.get_width() // 2, hint_y_start + 40 + i * 25))