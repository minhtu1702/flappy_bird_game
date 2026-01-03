import pygame
import os

class Bird:
    def __init__(self, x, y, bird_type="red"):
        self.x = x
        self.y = y
        self.velocity = 0
        # Tham số vật lý (có thể điều chỉnh để thay đổi cảm giác chơi)
        # `gravity`: lực kéo xuống mỗi frame
        self.gravity = 0.38
        # `angle`: góc hiển thị của chim (dùng để xoay sprite)
        self.angle = 0
        # `animation_time`: bộ đếm để thay đổi khung hoạt hình
        self.animation_time = 0
        # `max_fall_speed`: giới hạn tốc độ rơi để dễ kiểm soát
        self.max_fall_speed = 10.0
        # `up_flap_strength`: lực đẩy khi ấn flap (số âm để hướng lên)
        self.up_flap_strength = -7.0
        # `drag`: ma sát nhẹ làm mượt sự thay đổi vận tốc
        self.drag = 0.996
        self.bird_type = bird_type

        # load images based on bird_type
        self.images = []
        
        # If a skin file is provided, use that exact image to construct
        # gameplay animation frames (slight roto variants) so the bird
        # in-game visually matches the chosen preview.
        if isinstance(bird_type, str) and bird_type.endswith('.png'):
            try:
                skin_img = pygame.image.load(bird_type).convert_alpha()
                skin_img = pygame.transform.scale(skin_img, (34, 24))

                # Create three frames from the skin to simulate flapping:
                # center, slight up-tilt, slight down-tilt.
                frame_center = skin_img
                frame_up = pygame.transform.rotozoom(skin_img, 6, 1.0)
                frame_down = pygame.transform.rotozoom(skin_img, -6, 1.0)

                # Ensure frames have same size by centering onto surfaces
                w, h = 34, 24
                def fit_frame(img):
                    surf = pygame.Surface((w, h), pygame.SRCALPHA)
                    r = img.get_rect(center=(w//2, h//2))
                    surf.blit(img, r)
                    return surf

                self.images = [fit_frame(frame_center), fit_frame(frame_up), fit_frame(frame_down)]
            except Exception as e:
                print(f"Error loading skin {bird_type}: {e}")
                print(f"Current directory: {os.getcwd()}")
                # Fallback to animated default bird
                self.load_default_bird()
        else:
            # Load base images (red/blue/yellow animation frames)
            self.load_default_bird()

        self.image_index = 0
        self.image = self.images[self.image_index]

    def load_default_bird(self, tint_color=None):
        """Load the default red bird animation frames and optionally tint them.

        If `tint_color` is provided it will be applied to all frames. Otherwise
        the `self.bird_type` is used to pick a tint (red/blue/yellow) as before.
        """
        """Load the default red bird animation frames and optionally tint them.

        If `tint_color` is provided it will be applied to all frames. Otherwise
        the `self.bird_type` is used to pick a tint (red/blue/yellow) as before.
        """
        # Tải 3 khung ảnh mặc định (up/mid/down) để làm hoạt ảnh vỗ cánh
        base_images = [
            pygame.image.load("../assets/images/redbird-upflap.png").convert_alpha(),
            pygame.image.load("../assets/images/redbird-midflap.png").convert_alpha(),
            pygame.image.load("../assets/images/redbird-downflap.png").convert_alpha()
        ]

        # tint colors default map (used only if tint_color not explicitly provided)
        default_colors = {
            "red": (255, 0, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0)
        }

        if tint_color is None:
            tint_color = default_colors.get(self.bird_type, None)

        for img in base_images:
            if tint_color is None:
                self.images.append(img)
            else:
                tinted = img.copy()
                tinted.fill(tint_color, special_flags=pygame.BLEND_MULT)
                self.images.append(tinted)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.flap()

    def flap(self):
        # Người chơi nhấn SPACE -> chim vỗ cánh
        # Áp lực vỗ cánh là `self.up_flap_strength` (giá trị âm để bắn chim lên)
        self.velocity = self.up_flap_strength
        # Khi vỗ cánh, chim nghiêng lên nhẹ để nhìn tự nhiên
        self.angle = 25

    def update(self):
        # Cập nhật vận tốc với trọng lực
        self.velocity += self.gravity

        # Giới hạn tốc độ rơi để người chơi không mất kiểm soát
        if self.velocity > self.max_fall_speed:
            self.velocity = self.max_fall_speed

        # Ma sát không khí nhẹ giúp chuyển đổi vận tốc mượt mà hơn
        self.velocity *= self.drag

        # Cập nhật vị trí theo vận tốc
        self.y += self.velocity

        # Tính góc hiển thị dựa trên vận tốc: khi bay lên thì nghiêng lên,
        # khi rơi sẽ dần nghiêng xuống tới -90 độ. Dùng nội suy (lerp) cho mượt.
        if self.velocity < 0:
            target_angle = 25
        else:
            ratio = min(1.0, self.velocity / self.max_fall_speed)
            target_angle = -90 * ratio
        self.angle += (target_angle - self.angle) * 0.12

        # animation chim
        self.animation_time += 1
        if self.animation_time % 5 == 0:  # thay đổi hình mỗi 5 frame
            self.image_index = (self.image_index + 1) % 3
            self.image = self.images[self.image_index]

    def draw(self, screen):
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        rect = rotated_image.get_rect(center=(self.x + self.image.get_width() // 2, self.y + self.image.get_height() // 2))
        screen.blit(rotated_image, rect)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.image.get_width(), self.image.get_height())
