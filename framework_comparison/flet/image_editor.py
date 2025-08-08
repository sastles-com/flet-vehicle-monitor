import flet as ft
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import io
import base64
import os
from typing import Optional


class ImageEditor:
    def __init__(self):
        self.current_image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.image_display: Optional[ft.Image] = None
        self.file_name: str = ""
        
    def pil_to_base64(self, img: Image.Image) -> str:
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def update_display(self):
        if self.current_image and self.image_display:
            self.image_display.src_base64 = self.pil_to_base64(self.current_image)
            self.image_display.update()
    
    def load_image(self, file_path: str):
        try:
            self.original_image = Image.open(file_path).convert("RGBA")
            self.current_image = self.original_image.copy()
            self.file_name = os.path.basename(file_path)
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def save_image(self, file_path: str):
        if self.current_image:
            try:
                if file_path.lower().endswith('.png'):
                    self.current_image.save(file_path, "PNG")
                else:
                    rgb_image = self.current_image.convert("RGB")
                    rgb_image.save(file_path, "JPEG")
                return True
            except Exception as e:
                print(f"Error saving image: {e}")
                return False
        return False
    
    def reset_image(self):
        if self.original_image:
            self.current_image = self.original_image.copy()
            self.update_display()
    
    def resize_image(self, width: int, height: int):
        if self.current_image:
            self.current_image = self.current_image.resize((width, height), Image.Resampling.LANCZOS)
            self.update_display()
    
    def rotate_image(self, angle: float):
        if self.current_image:
            self.current_image = self.current_image.rotate(-angle, expand=True, fillcolor=(255, 255, 255, 0))
            self.update_display()
    
    def flip_horizontal(self):
        if self.current_image:
            self.current_image = ImageOps.mirror(self.current_image)
            self.update_display()
    
    def flip_vertical(self):
        if self.current_image:
            self.current_image = ImageOps.flip(self.current_image)
            self.update_display()
    
    def apply_blur(self):
        if self.current_image:
            self.current_image = self.current_image.filter(ImageFilter.BLUR)
            self.update_display()
    
    def apply_sharpen(self):
        if self.current_image:
            self.current_image = self.current_image.filter(ImageFilter.SHARPEN)
            self.update_display()
    
    def apply_contour(self):
        if self.current_image:
            self.current_image = self.current_image.filter(ImageFilter.CONTOUR)
            self.update_display()
    
    def apply_emboss(self):
        if self.current_image:
            self.current_image = self.current_image.filter(ImageFilter.EMBOSS)
            self.update_display()
    
    def adjust_brightness(self, factor: float):
        if self.current_image:
            enhancer = ImageEnhance.Brightness(self.current_image)
            self.current_image = enhancer.enhance(factor)
            self.update_display()
    
    def adjust_contrast(self, factor: float):
        if self.current_image:
            enhancer = ImageEnhance.Contrast(self.current_image)
            self.current_image = enhancer.enhance(factor)
            self.update_display()
    
    def adjust_saturation(self, factor: float):
        if self.current_image:
            enhancer = ImageEnhance.Color(self.current_image)
            self.current_image = enhancer.enhance(factor)
            self.update_display()
    
    def convert_grayscale(self):
        if self.current_image:
            self.current_image = ImageOps.grayscale(self.current_image).convert("RGBA")
            self.update_display()


def main(page: ft.Page):
    page.title = "Image Editor"
    page.window_width = 1200
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.LIGHT
    
    editor = ImageEditor()
    
    def on_file_selected(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            if editor.load_image(file_path):
                editor.image_display = image_view
                editor.update_display()
                image_container.visible = True
                controls_container.visible = True
                page.update()
                show_snackbar(f"Loaded: {editor.file_name}")
            else:
                show_snackbar("Failed to load image", error=True)
    
    def on_save_result(e: ft.FilePickerResultEvent):
        if e.path:
            if editor.save_image(e.path):
                show_snackbar(f"Saved to: {e.path}")
            else:
                show_snackbar("Failed to save image", error=True)
    
    def show_snackbar(message: str, error: bool = False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400,
        )
        page.snack_bar.open = True
        page.update()
    
    file_picker = ft.FilePicker(
        on_result=on_file_selected,
    )
    
    save_picker = ft.FilePicker(
        on_result=on_save_result,
    )
    
    page.overlay.extend([file_picker, save_picker])
    
    image_view = ft.Image(
        width=600,
        height=400,
        fit=ft.ImageFit.CONTAIN,
    )
    
    def on_resize_click(e):
        if editor.current_image:
            try:
                width = int(width_field.value)
                height = int(height_field.value)
                editor.resize_image(width, height)
                show_snackbar(f"Resized to {width}x{height}")
            except ValueError:
                show_snackbar("Invalid dimensions", error=True)
    
    def on_rotate_click(e):
        try:
            angle = float(rotate_field.value)
            editor.rotate_image(angle)
            show_snackbar(f"Rotated {angle}°")
        except ValueError:
            show_snackbar("Invalid angle", error=True)
    
    def on_brightness_change(e):
        editor.adjust_brightness(e.control.value)
    
    def on_contrast_change(e):
        editor.adjust_contrast(e.control.value)
    
    def on_saturation_change(e):
        editor.adjust_saturation(e.control.value)
    
    width_field = ft.TextField(label="Width", width=100, value="800")
    height_field = ft.TextField(label="Height", width=100, value="600")
    rotate_field = ft.TextField(label="Angle", width=100, value="90")
    
    brightness_slider = ft.Slider(
        min=0.5, max=2.0, value=1.0, label="Brightness",
        on_change=on_brightness_change,
        width=200,
    )
    
    contrast_slider = ft.Slider(
        min=0.5, max=2.0, value=1.0, label="Contrast",
        on_change=on_contrast_change,
        width=200,
    )
    
    saturation_slider = ft.Slider(
        min=0, max=2.0, value=1.0, label="Saturation",
        on_change=on_saturation_change,
        width=200,
    )
    
    image_container = ft.Container(
        content=image_view,
        bgcolor=ft.Colors.GREY_200,
        border_radius=10,
        padding=10,
        visible=False,
    )
    
    controls_container = ft.Container(
        content=ft.Column([
            ft.Text("Image Operations", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text("Transform", size=16, weight=ft.FontWeight.W_500),
            ft.Row([
                width_field,
                height_field,
                ft.ElevatedButton("Resize", on_click=on_resize_click),
            ]),
            ft.Row([
                rotate_field,
                ft.ElevatedButton("Rotate", on_click=on_rotate_click),
            ]),
            ft.Row([
                ft.ElevatedButton("Flip Horizontal", on_click=lambda _: editor.flip_horizontal()),
                ft.ElevatedButton("Flip Vertical", on_click=lambda _: editor.flip_vertical()),
            ]),
            
            ft.Divider(),
            ft.Text("Filters", size=16, weight=ft.FontWeight.W_500),
            ft.Row([
                ft.ElevatedButton("Blur", on_click=lambda _: editor.apply_blur()),
                ft.ElevatedButton("Sharpen", on_click=lambda _: editor.apply_sharpen()),
                ft.ElevatedButton("Contour", on_click=lambda _: editor.apply_contour()),
                ft.ElevatedButton("Emboss", on_click=lambda _: editor.apply_emboss()),
                ft.ElevatedButton("Grayscale", on_click=lambda _: editor.convert_grayscale()),
            ], wrap=True),
            
            ft.Divider(),
            ft.Text("Adjustments", size=16, weight=ft.FontWeight.W_500),
            ft.Row([ft.Text("Brightness:"), brightness_slider]),
            ft.Row([ft.Text("Contrast:"), contrast_slider]),
            ft.Row([ft.Text("Saturation:"), saturation_slider]),
            
            ft.Divider(),
            ft.Row([
                ft.ElevatedButton(
                    "Reset",
                    on_click=lambda _: editor.reset_image(),
                    bgcolor=ft.Colors.ORANGE_400,
                ),
                ft.ElevatedButton(
                    "Save As",
                    on_click=lambda _: save_picker.save_file(
                        dialog_title="Save Image",
                        file_name=f"edited_{editor.file_name}",
                        allowed_extensions=["png", "jpg", "jpeg"],
                    ),
                    bgcolor=ft.Colors.GREEN_400,
                ),
            ]),
        ], scroll=ft.ScrollMode.AUTO),
        width=400,
        padding=20,
        visible=False,
    )
    
    app_bar = ft.AppBar(
        leading=ft.Icon(ft.icons.IMAGE),
        leading_width=40,
        title=ft.Text("Python Image Editor"),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_VARIANT,
        actions=[
            ft.IconButton(
                ft.icons.FOLDER_OPEN,
                on_click=lambda _: file_picker.pick_files(
                    dialog_title="Select an image",
                    allowed_extensions=["png", "jpg", "jpeg", "gif", "bmp"],
                ),
                tooltip="Open Image",
            ),
        ],
    )
    
    page.add(
        app_bar,
        ft.Row([
            ft.Container(
                content=image_container,
                expand=True,
                padding=20,
            ),
            controls_container,
        ], expand=True),
    )
    
    if not editor.current_image:
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.IMAGE, size=100, color=ft.Colors.GREY_400),
                    ft.Text("Click the folder icon to open an image", size=18, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True,
            )
        )


if __name__ == "__main__":
    ft.app(target=main)