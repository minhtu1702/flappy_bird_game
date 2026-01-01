import pygame
import random
import os
import sys

# Khởi tạo Pygame
pygame.init()

# Đường dẫn đến thư mục assets
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')

# Cài đặt màn hình
FULLSCREEN_MODE = True  # Đặt True để chơi fullscreen, False để chơi cửa sổ
WINDOW_WIDTH = 800      # Chiều rộng cửa sổ (nếu không fullscreen)
WINDOW_HEIGHT = 600     # Chiều cao cửa sổ (nếu không fullscreen)

# Lấy kích thước màn hình thực
if FULLSCREEN_MODE:
    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w
    SCREEN_HEIGHT = info.current_h
else:
    SCREEN_WIDTH = WINDOW_WIDTH
    SCREEN_HEIGHT = WINDOW_HEIGHT

# Hằng số game (tự động scale theo kích thước màn hình)
FPS = 60
GRAVITY = 0.4 * (SCREEN_HEIGHT / 600)  # Scale theo chiều cao
JUMP_STRENGTH = -8 * (SCREEN_HEIGHT / 600)
PIPE_SPEED = 2.5 * (SCREEN_WIDTH / 400)  # Scale theo chiều rộng
PIPE_SPEED_INCREMENT = 0.15 * (SCREEN_WIDTH / 400)
MAX_PIPE_SPEED = 5.0 * (SCREEN_WIDTH / 400)
PIPE_GAP = int(180 * (SCREEN_HEIGHT / 600))
PIPE_GAP_DECREMENT = int(3 * (SCREEN_HEIGHT / 600))
MIN_PIPE_GAP = int(140 * (SCREEN_HEIGHT / 600))
PIPE_SPAWN_DISTANCE = int(350 * (SCREEN_WIDTH / 400))

# Kích thước ống CỐ ĐỊNH (không scale) để hiển thị nhiều ống hơn khi màn hình to
PIPE_WIDTH = 60  # Giữ nguyên 60 pixels cho mọi kích thước màn hình

# Màu sắc
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)


class AssetManager:
    """Class quản lý tải và lưu trữ tất cả tài nguyên (ảnh, âm thanh)"""
    
    def __init__(self):
        self.number_images = {}  # Dictionary lưu ảnh số từ 0-9
        self.bird_frames = []  # List chứa các frame animation của bird
        self.pipe_image = None
        self.background_image = None
        
        # Dictionary lưu các âm thanh
        self.sounds = {}
        
        # Load tất cả assets
        self._load_number_images()
        self._load_game_images()
        self._load_sounds()
    
    def _load_number_images(self):
        """Load ảnh số từ 0-9"""
        for i in range(10):
            filename = os.path.join(ASSETS_DIR, f"{i}.png")
            try:
                if os.path.exists(filename):
                    img = pygame.image.load(filename).convert_alpha()
                    # Giữ nguyên tỷ lệ nhưng scale lên 2x cho dễ nhìn
                    original_size = img.get_size()
                    new_size = (original_size[0] * 2, original_size[1] * 2)
                    img = pygame.transform.scale(img, new_size)
                    self.number_images[i] = img
                    print(f"✓ Loaded {i}.png")
                else:
                    # Tạo ảnh số dự phòng nếu không tìm thấy file
                    self.number_images[i] = self._create_fallback_number(i)
                    print(f"✗ {i}.png not found, using fallback")
            except Exception as e:
                print(f"Error loading {i}.png: {e}")
                self.number_images[i] = self._create_fallback_number(i)
    
    def _create_fallback_number(self, number):
        """Tạo ảnh số dự phòng bằng text"""
        font = pygame.font.Font(None, 40)
        text_surface = font.render(str(number), True, WHITE)
        return text_surface
    
    def _load_game_images(self):
        """Load ảnh các đối tượng game (bird, pipe, background)"""
        # Load bird animation frames (3 frames)
        bird_filenames = [
            "redbird-downflap.png",
            "redbird-midflap.png", 
            "redbird-upflap.png"
        ]
        
        # Kích thước bird CỐ ĐỊNH (không scale quá lớn)
        # Scale nhẹ theo chiều cao màn hình nhưng giữ tỷ lệ hợp lý
        bird_scale = min(3, max(2, int(SCREEN_HEIGHT / 300)))
        
        for filename in bird_filenames:
            filepath = os.path.join(ASSETS_DIR, filename)
            try:
                if os.path.exists(filepath):
                    img = pygame.image.load(filepath).convert_alpha()
                    # Scale bird vừa phải
                    original_size = img.get_size()
                    img = pygame.transform.scale(img, (original_size[0] * 2, original_size[1] * 2))
                    self.bird_frames.append(img)
                    print(f"✓ Loaded {filename}")
            except Exception as e:
                print(f"✗ Could not load {filename}: {e}")
        
        # Nếu không load được bird frames, dùng fallback
        if len(self.bird_frames) == 0:
            print("Using fallback bird")
        
        # Load pipe image
        pipe_path = os.path.join(ASSETS_DIR, "pipe-green.png")
        try:
            if os.path.exists(pipe_path):
                self.pipe_image = pygame.image.load(pipe_path).convert_alpha()
                print("✓ Loaded pipe-green.png")
        except Exception as e:
            print(f"✗ Could not load pipe-green.png: {e}")
        
        # Load background image
        bg_path = os.path.join(ASSETS_DIR, "background-black.png")
        try:
            if os.path.exists(bg_path):
                self.background_image = pygame.image.load(bg_path).convert_alpha()
                # Tile background để lấp đầy màn hình
                bg_width = self.background_image.get_width()
                bg_height = self.background_image.get_height()
                
                # Tạo surface mới cho background
                full_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                
                # Tile background theo chiều ngang và dọc
                for y in range(0, SCREEN_HEIGHT, bg_height):
                    for x in range(0, SCREEN_WIDTH, bg_width):
                        full_bg.blit(self.background_image, (x, y))
                
                self.background_image = full_bg
                print("✓ Loaded background-black.png")
        except Exception as e:
            print(f"✗ Could not load background-black.png: {e}")
        
        # Load base (đất) - KHÔNG SCALE CHIỀU CAO, chỉ tile theo chiều ngang
        self.base_image = None
        base_path = os.path.join(ASSETS_DIR, "base.png")
        try:
            if os.path.exists(base_path):
                base_img = pygame.image.load(base_path).convert_alpha()
                # GIỮ NGUYÊN chiều cao gốc của base
                base_height = base_img.get_height()
                base_width = base_img.get_width()
                
                # Tạo base đủ rộng cho cả màn hình (tile theo chiều ngang)
                tiles_needed = (SCREEN_WIDTH // base_width) + 2
                total_width = base_width * tiles_needed
                
                self.base_image = pygame.Surface((total_width, base_height), pygame.SRCALPHA)
                for i in range(tiles_needed):
                    self.base_image.blit(base_img, (i * base_width, 0))
                
                print(f"✓ Loaded base.png (height: {base_height}px)")
        except Exception as e:
            print(f"✗ Could not load base.png: {e}")
    
    def _load_sounds(self):
        """Load các file âm thanh .ogg"""
        # Danh sách các file âm thanh cần load
        sound_files = {
            'wing': 'wing.ogg',          # Âm thanh vỗ cánh/nhảy
            'point': 'point.ogg',        # Âm thanh ghi điểm
            'hit': 'hit.ogg',            # Âm thanh va chạm
            'die': 'die.ogg',            # Âm thanh chết
            'swoosh': 'swoosh.ogg',      # Âm thanh swoosh
        }
        
        for sound_name, filename in sound_files.items():
            filepath = os.path.join(ASSETS_DIR, filename)
            try:
                if os.path.exists(filepath):
                    sound = pygame.mixer.Sound(filepath)
                    self.sounds[sound_name] = sound
                    print(f"✓ Loaded {filename}")
            except Exception as e:
                print(f"✗ Could not load {filename}: {e}")
    
    def play_sound(self, sound_name):
        """Play âm thanh theo tên"""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()


class Bird:
    """Class quản lý chim (player)"""
    
    def __init__(self, x, y, asset_manager):
        self.x = x
        self.y = y
        self.velocity = 0  # Vận tốc theo trục y
        self.asset_manager = asset_manager
        
        # Animation
        self.frame_index = 0
        self.animation_counter = 0
        self.animation_speed = 5  # Đổi frame sau mỗi 5 ticks
        
        # Kích thước bird (GIỮ NGUYÊN từ ảnh, không scale quá mức)
        if len(self.asset_manager.bird_frames) > 0:
            bird_size = self.asset_manager.bird_frames[0].get_size()
            self.width = bird_size[0]
            self.height = bird_size[1]
        else:
            # Fallback size CỐ ĐỊNH
            self.width = 68  # 34 * 2 (scale 2x)
            self.height = 48  # 24 * 2 (scale 2x)
        
        # Tạo rect để collision detection
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Góc xoay cho animation
        self.rotation = 0
    
    def jump(self):
        """Thực hiện hành động nhảy"""
        self.velocity = JUMP_STRENGTH
        self.rotation = 25  # Ngẩng đầu lên khi nhảy
        
        # Play âm thanh nhảy
        if 'wing' in self.asset_manager.sounds:
            self.asset_manager.play_sound('wing')
    
    def update(self):
        """Cập nhật vị trí và vận tốc của bird"""
        # Áp dụng trọng lực
        self.velocity += GRAVITY
        self.y += self.velocity
        
        # Giới hạn vận tốc rơi tối đa (giảm từ 10 → 8)
        if self.velocity > 8:
            self.velocity = 8
        
        # Cập nhật góc xoay dựa trên vận tốc
        if self.velocity < 0:
            self.rotation = 25
        elif self.velocity > 2:
            self.rotation = max(-90, self.rotation - 2.5)  # Xoay chậm hơn (từ 3 → 2.5)
        
        # Cập nhật animation
        self.animation_counter += 1
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.frame_index = (self.frame_index + 1) % max(1, len(self.asset_manager.bird_frames))
        
        # Cập nhật rect
        self.rect.y = self.y
    
    def draw(self, screen):
        """Vẽ bird lên màn hình với animation"""
        if len(self.asset_manager.bird_frames) > 0:
            # Lấy frame hiện tại
            current_frame = self.asset_manager.bird_frames[self.frame_index]
            
            # Xoay bird theo góc
            rotated_bird = pygame.transform.rotate(current_frame, self.rotation)
            rotated_rect = rotated_bird.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
            
            # Vẽ bird
            screen.blit(rotated_bird, rotated_rect)
        else:
            # Fallback: vẽ hình chữ nhật màu vàng
            pygame.draw.rect(screen, YELLOW, self.rect)
            # Vẽ viền đen
            pygame.draw.rect(screen, BLACK, self.rect, 2)
    
    def get_mask(self):
        """Tạo mask cho collision detection chính xác"""
        if len(self.asset_manager.bird_frames) > 0:
            return pygame.mask.from_surface(self.asset_manager.bird_frames[self.frame_index])
        return None


class Pipe:
    """Class quản lý cặp ống (trên và dưới)"""
    
    def __init__(self, x, asset_manager, current_speed, current_gap):
        self.x = x
        self.asset_manager = asset_manager
        self.speed = current_speed  # Tốc độ của ống này
        
        # Thêm biến thể ngẫu nhiên cho gap size (±10%)
        gap_variation = random.randint(-int(current_gap * 0.1), int(current_gap * 0.1))
        self.gap_size = current_gap + gap_variation
        
        # Kích thước ống CỐ ĐỊNH (60px như màn hình nhỏ)
        self.width = PIPE_WIDTH
        
        # Tính chiều cao của base (nền cỏ) nếu có
        base_height = 0
        if self.asset_manager.base_image:
            base_height = self.asset_manager.base_image.get_height()
        
        # Tạo khoảng trống ngẫu nhiên cho bird bay qua
        # Mở rộng phạm vi ngẫu nhiên để đa dạng hơn
        min_gap_y = int(80 * (SCREEN_HEIGHT / 600))   # Giảm từ 100 → 80
        max_gap_y = SCREEN_HEIGHT - base_height - self.gap_size - int(80 * (SCREEN_HEIGHT / 600))
        
        # Đảm bảo max_gap_y không nhỏ hơn min_gap_y
        if max_gap_y < min_gap_y:
            max_gap_y = min_gap_y + int(50 * (SCREEN_HEIGHT / 600))
        
        # Tăng độ ngẫu nhiên: ưu tiên các vị trí khác nhau
        # 30% ống cao, 40% ống giữa, 30% ống thấp
        rand_type = random.random()
        if rand_type < 0.3:  # Ống cao (bird bay thấp)
            range_size = (max_gap_y - min_gap_y) // 3
            self.gap_y = random.randint(min_gap_y, min_gap_y + range_size)
        elif rand_type < 0.7:  # Ống giữa (cân bằng)
            range_size = (max_gap_y - min_gap_y) // 3
            middle_start = min_gap_y + range_size
            self.gap_y = random.randint(middle_start, middle_start + range_size)
        else:  # Ống thấp (bird bay cao)
            range_size = (max_gap_y - min_gap_y) // 3
            low_start = max_gap_y - range_size
            self.gap_y = random.randint(low_start, max_gap_y)
        
        # Tạo rect cho ống trên và ống dưới
        self.top_rect = pygame.Rect(self.x, 0, self.width, self.gap_y)
        
        # Ống dưới không được vượt quá vị trí nền cỏ
        bottom_y = self.gap_y + self.gap_size
        bottom_height = SCREEN_HEIGHT - base_height - bottom_y
        
        # Đảm bảo ống dưới có chiều cao tối thiểu
        min_bottom_height = int(50 * (SCREEN_HEIGHT / 600))
        if bottom_height < min_bottom_height:
            bottom_height = min_bottom_height
            bottom_y = SCREEN_HEIGHT - base_height - bottom_height
        
        self.bottom_rect = pygame.Rect(
            self.x, 
            bottom_y, 
            self.width, 
            bottom_height
        )
        
        # Flag để kiểm tra đã tính điểm chưa
        self.passed = False
    
    def update(self):
        """Di chuyển ống sang trái"""
        self.x -= self.speed
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x
    
    def draw(self, screen):
        """Vẽ cặp ống lên màn hình"""
        if self.asset_manager.pipe_image:
            # Nếu có ảnh pipe
            # Ống trên (flip ảnh)
            pipe_top = pygame.transform.flip(self.asset_manager.pipe_image, False, True)
            pipe_top = pygame.transform.scale(pipe_top, (self.width, self.gap_y))
            screen.blit(pipe_top, (self.x, 0))
            
            # Ống dưới
            pipe_bottom = pygame.transform.scale(
                self.asset_manager.pipe_image, 
                (self.width, self.bottom_rect.height)
            )
            screen.blit(pipe_bottom, (self.x, self.gap_y + self.gap_size))
        else:
            # Fallback: vẽ hình chữ nhật màu xanh lá
            pygame.draw.rect(screen, GREEN, self.top_rect)
            pygame.draw.rect(screen, GREEN, self.bottom_rect)
            # Vẽ viền
            pygame.draw.rect(screen, BLACK, self.top_rect, 2)
            pygame.draw.rect(screen, BLACK, self.bottom_rect, 2)
    
    def is_off_screen(self):
        """Kiểm tra xem ống đã ra khỏi màn hình chưa"""
        return self.x + self.width < 0
    
    def collides_with(self, bird):
        """Kiểm tra va chạm với bird (Box collision)"""
        return (self.top_rect.colliderect(bird.rect) or 
                self.bottom_rect.colliderect(bird.rect))


class ScoreBoard:
    """Class quản lý hiển thị điểm số"""
    
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        self.score = 0
    
    def increment(self):
        """Tăng điểm lên 1"""
        self.score += 1
    
    def reset(self):
        """Reset điểm về 0"""
        self.score = 0
    
    def draw(self, screen):
        """Vẽ điểm số lên màn hình (căn giữa ở phía trên)"""
        # Chuyển điểm số thành string để tách các chữ số
        score_str = str(self.score)
        
        # Lấy kích thước của ảnh số để tính toán
        digit_width = self.asset_manager.number_images[0].get_width()
        digit_height = self.asset_manager.number_images[0].get_height()
        spacing = 5  # Khoảng cách giữa các số
        
        # Tính tổng chiều rộng của tất cả các chữ số
        total_width = len(score_str) * digit_width + (len(score_str) - 1) * spacing
        
        # Vị trí bắt đầu để căn giữa
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = 50  # Vị trí y cố định ở trên cùng
        
        # Vẽ từng chữ số
        for i, digit_char in enumerate(score_str):
            digit = int(digit_char)
            digit_image = self.asset_manager.number_images[digit]
            x = start_x + i * (digit_width + spacing)
            screen.blit(digit_image, (x, y))


class Game:
    """Class chính quản lý game loop và trạng thái game"""
    
    def __init__(self):
        # Tạo màn hình với chế độ fullscreen hoặc windowed
        if FULLSCREEN_MODE:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
            print(f"✓ Fullscreen mode: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            print(f"✓ Windowed mode: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        
        pygame.display.set_caption("Flappy Bird - OOP")
        
        # Clock để kiểm soát FPS
        self.clock = pygame.time.Clock()
        
        # Load assets
        self.asset_manager = AssetManager()
        
        # Game state
        self.state = "START"  # START, PLAYING, GAME_OVER
        
        # Độ khó động (Dynamic Difficulty)
        self.current_pipe_speed = PIPE_SPEED
        self.current_pipe_gap = PIPE_GAP
        
        # Vị trí bird (căn giữa theo chiều ngang, scaled)
        bird_x = int(SCREEN_WIDTH * 0.2)  # 20% từ bên trái
        bird_y = SCREEN_HEIGHT // 2
        
        # Khởi tạo các đối tượng game
        self.bird = Bird(bird_x, bird_y, self.asset_manager)
        self.pipes = []
        self.scoreboard = ScoreBoard(self.asset_manager)
        
        # Base scrolling (cho hiệu ứng di chuyển)
        self.base_x = 0
        
        # Tạo ống đầu tiên
        self.pipes.append(Pipe(SCREEN_WIDTH, self.asset_manager, self.current_pipe_speed, self.current_pipe_gap))
        
        # Font cho text (scaled theo màn hình)
        font_size_large = int(48 * (SCREEN_HEIGHT / 600))
        font_size_small = int(32 * (SCREEN_HEIGHT / 600))
        self.font = pygame.font.Font(None, font_size_large)
        self.small_font = pygame.font.Font(None, font_size_small)
        
        self.running = True
    
    def handle_events(self):
        """Xử lý các sự kiện (input)"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                # ESC để thoát fullscreen hoặc thoát game
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # F11 để toggle fullscreen
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                
                if event.key == pygame.K_SPACE:
                    if self.state == "START":
                        # Bắt đầu game
                        self.state = "PLAYING"
                        self.bird.jump()
                    elif self.state == "PLAYING":
                        # Nhảy
                        self.bird.jump()
                    elif self.state == "GAME_OVER":
                        # Restart game
                        self.restart()
    
    def update_difficulty(self):
        """Cập nhật độ khó dựa trên điểm số"""
        score = self.scoreboard.score
        
        # Tăng tốc độ sau mỗi 5 điểm (nhưng không vượt quá max)
        speed_increase = (score // 5) * PIPE_SPEED_INCREMENT
        self.current_pipe_speed = min(PIPE_SPEED + speed_increase, MAX_PIPE_SPEED)
        
        # Giảm khoảng trống sau mỗi 10 điểm (nhưng không nhỏ hơn min)
        gap_decrease = (score // 10) * PIPE_GAP_DECREMENT
        self.current_pipe_gap = max(PIPE_GAP - gap_decrease, MIN_PIPE_GAP)
    
    def update(self):
        """Cập nhật logic game"""
        if self.state == "PLAYING":
            # Cập nhật độ khó
            self.update_difficulty()
            
            # Tính chiều cao của base (nền cỏ)
            base_height = 0
            if self.asset_manager.base_image:
                base_height = self.asset_manager.base_image.get_height()
            
            # Cập nhật bird
            self.bird.update()
            
            # Kiểm tra bird chạm nền cỏ hoặc bay quá cao
            ground_level = SCREEN_HEIGHT - base_height
            if self.bird.y + self.bird.height > ground_level or self.bird.y < 0:
                self.state = "GAME_OVER"
                
                # Giới hạn bird không rơi xuống dưới nền cỏ
                if self.bird.y + self.bird.height > ground_level:
                    self.bird.y = ground_level - self.bird.height
                
                # Play âm thanh va chạm
                if 'hit' in self.asset_manager.sounds:
                    self.asset_manager.play_sound('hit')
            
            # Cập nhật pipes
            for pipe in self.pipes:
                pipe.update()
                
                # Kiểm tra va chạm
                if pipe.collides_with(self.bird):
                    self.state = "GAME_OVER"
                    
                    # Play âm thanh va chạm
                    if 'hit' in self.asset_manager.sounds:
                        self.asset_manager.play_sound('hit')
                    if 'die' in self.asset_manager.sounds:
                        self.asset_manager.play_sound('die')
                
                # Kiểm tra bird đã bay qua ống chưa (để tính điểm)
                if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                    pipe.passed = True
                    self.scoreboard.increment()
                    
                    # Play âm thanh ghi điểm
                    if 'point' in self.asset_manager.sounds:
                        self.asset_manager.play_sound('point')
            
            # Xóa ống đã ra khỏi màn hình
            self.pipes = [pipe for pipe in self.pipes if not pipe.is_off_screen()]
            
            # Tạo ống mới khi cần (với tốc độ và gap hiện tại)
            if len(self.pipes) == 0 or self.pipes[-1].x < SCREEN_WIDTH - PIPE_SPAWN_DISTANCE:
                # Thêm biến thể khoảng cách giữa các ống (±15%)
                distance_variation = random.randint(
                    -int(PIPE_SPAWN_DISTANCE * 0.15), 
                    int(PIPE_SPAWN_DISTANCE * 0.15)
                )
                spawn_x = SCREEN_WIDTH + distance_variation
                
                self.pipes.append(Pipe(spawn_x, self.asset_manager, self.current_pipe_speed, self.current_pipe_gap))
    
    def draw(self):
        """Vẽ tất cả các đối tượng lên màn hình"""
        # Vẽ background
        if self.asset_manager.background_image:
            self.screen.blit(self.asset_manager.background_image, (0, 0))
        else:
            # Fallback: màu xanh da trời
            self.screen.fill(BLUE)
        
        # Vẽ pipes
        for pipe in self.pipes:
            pipe.draw(self.screen)
        
        # Vẽ base (đất) nếu có với scrolling effect
        if self.asset_manager.base_image:
            base_y = SCREEN_HEIGHT - self.asset_manager.base_image.get_height()
            
            # Vẽ 2 lần để tạo hiệu ứng scroll vô tận
            self.screen.blit(self.asset_manager.base_image, (self.base_x, base_y))
            self.screen.blit(self.asset_manager.base_image, (self.base_x + SCREEN_WIDTH, base_y))
            
            # Update base position cho scrolling effect
            if self.state == "PLAYING":
                self.base_x -= self.current_pipe_speed
                if self.base_x <= -SCREEN_WIDTH:
                    self.base_x = 0
        
        # Vẽ bird
        self.bird.draw(self.screen)
        
        # Vẽ điểm số
        self.scoreboard.draw(self.screen)
        
        # Hiển thị tốc độ hiện tại (debug info)
        if self.state == "PLAYING":
            speed_text = self.small_font.render(f"Speed: {self.current_pipe_speed:.1f}x", True, WHITE)
            self.screen.blit(speed_text, (10, 10))
            gap_text = self.small_font.render(f"Gap: {self.current_pipe_gap}", True, WHITE)
            self.screen.blit(gap_text, (10, 40))
            
            # Hiển thị FPS
            fps_text = self.small_font.render(f"FPS: {int(self.clock.get_fps())}", True, WHITE)
            self.screen.blit(fps_text, (10, 70))
        
        # Vẽ UI theo state
        if self.state == "START":
            text = self.font.render("Press SPACE to Start", True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)
            
            # Hướng dẫn controls
            control_text = self.small_font.render("ESC: Exit | F11: Toggle Fullscreen", True, WHITE)
            control_rect = control_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(control_text, control_rect)
        
        elif self.state == "GAME_OVER":
            # Game Over text
            text = self.font.render("GAME OVER", True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(text, text_rect)
            
            # Score text
            score_text = self.small_font.render(f"Score: {self.scoreboard.score}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(score_text, score_rect)
            
            # Restart instruction
            restart_text = self.small_font.render("Press SPACE to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(restart_text, restart_rect)
        
        # Cập nhật màn hình
        pygame.display.flip()
    
    def restart(self):
        """Khởi động lại game"""
        self.state = "START"
        
        # Vị trí bird (căn giữa theo chiều ngang)
        bird_x = int(SCREEN_WIDTH * 0.2)
        bird_y = SCREEN_HEIGHT // 2
        
        self.bird = Bird(bird_x, bird_y, self.asset_manager)
        
        # Reset độ khó về mức ban đầu
        self.current_pipe_speed = PIPE_SPEED
        self.current_pipe_gap = PIPE_GAP
        
        # Reset base scrolling
        self.base_x = 0
        
        self.pipes = [Pipe(SCREEN_WIDTH, self.asset_manager, self.current_pipe_speed, self.current_pipe_gap)]
        self.scoreboard.reset()
    
    def run(self):
        """Vòng lặp chính của game"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
            # Giới hạn FPS
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


# Entry point
if __name__ == "__main__":
    game = Game()
    game.run()