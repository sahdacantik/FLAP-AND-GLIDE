from ursina import *
import os
import random

# PLAYER 
class Player(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.velocity_y = 0
        self.grounded = False
        self.jump_count = 0
        self.jumps_left = 2
        self.jump_height = 5
        self.jump_duration = 0.4
        self.max_jumps = 2
        self.jumping = False
        self._start_fall_sequence = None
        self.invincible = False

# PLAYER LOMPAT
    def jump(self):
        if not self.grounded and self.jumps_left <= 1:
            return

        if self._start_fall_sequence:
            self._start_fall_sequence.kill()

        if hasattr(self, 'y_animator'):
            self.y_animator.kill()

        self.jump_dust = Entity(model=Circle(), scale=.5, color=color.white33, position=self.position)
        self.jump_dust.animate_scale(3, duration=.3, curve=curve.linear)
        self.jump_dust.fade_out(duration=.2)
        destroy(self.jump_dust, 2.1)

        self.jumping = True
        self.jumps_left -= 1
        self.grounded = False

        target_y = self.y + self.jump_height
        duration = self.jump_duration

        self.animate_y(target_y, duration, resolution=30, curve=curve.out_expo)
        self._start_fall_sequence = invoke(self.start_fall, delay=duration)

# PLAYER JATOH
    def start_fall(self):
        if hasattr(self, 'y_animator'):
            self.y_animator.pause()
        self.jumping = False

# PLAYER MENDARAT
    def land(self):
        self.air_time = 0
        self.jumps_left = self.max_jumps
        self.grounded = True

app = Ursina()

# LOAD SCREEN
bg_load = Entity(model='quad', texture='assets/bg_load', scale=(16, 9), z=1)
loading = Entity(model=Animation('assets/loading'), fps=3, scale=(2, 2), y=-2, z=0.5)
loading_music = Audio('assets/loadingBar.mp3', loop=True)
loading_music.play()

# SCORE
score = 0
score_text = Text(f'Score: {score}', position=(-0.85, 0.45), scale=2, color=color.white)
score_increment_interval = 0.1 
score_time = 0
score_speedup = 0.001  

# SCORE TERTINGGI
best_score = 0
best_score_text = Text(f'Best Score: {best_score}', position=(-0.85, 0.35), scale=2, color=color.yellow)

# MENU
menu_background = Entity(model='quad', color=color.black, scale=(35, 20), z=5, visible=False)
start_button = Button(text='Start', scale=(0.2, 0.1), position=(0, 0.1), on_click=lambda: start_game(), visible=False)
quit_button = Button(text='Quit', scale=(0.2, 0.1), position=(0, -0.1), on_click=lambda: application.quit(), visible=False)

game_active = False

# MAIN SCREEN
def show_main_screen():
    global loading_music, pemain, ngejar, backgrounds, main_screen_active, score, score_time, music
    music = Audio('assets/music.mp3', loop=True)
    music.play()
    
    loading_music.stop()
    destroy(bg_load)
    destroy(loading)
    print("Loading screen closed")

    # Background for the main game
    bg = Entity(model='quad', texture='assets/Background', scale=(96, 24), z=1)
    bg2 = duplicate(bg, x=96, z=1)
    bg_dup = duplicate(bg, x=192, z=1)
    bg2_dup = duplicate(bg2, x=288, z=1)
    backgrounds = [bg, bg2, bg_dup, bg2_dup]

    # MENAMPILKAN PLAYER DAN MUSUH
    if not pemain:
        pemain = Player(model=Animation('assets/player'), fps=5, collider='box', scale=(5, 3), x=0, y=0, z=-0.45)
        print("Player entity created")

    if not ngejar:
        ngejar = Entity(model=Animation('assets/musuh'), fps=6, collider='box', scale=(5, 3), x=-10, y=0, z=-0.45)
        print("Enemy entity created")


    main_screen_active = True
    score = 0
    score_time = 0

# ENTITAS LAINNYA
pemain = None
ngejar = None
buff = None  
entities = {
    'alien': [],
    'ufo': [],
    'star': [],
    'sun': [],
    'awan': [],
    'buff': [],
    'moon': [],
    'pesawat': [],
    'rainbow' : []
}
backgrounds = []
main_screen_active = False

def spawn_entity(name, texture, x, y):
    if name == 'alien':
        scale_factor = 1  
    elif name == 'ufo':
        scale_factor = 0.1  
    elif name == 'star':
        scale_factor = 4
    elif name == 'sun':
        scale_factor = 1.5  
    elif name == 'awan':
        scale_factor = 2  
    elif name == 'buff':
        scale_factor = 1  
    elif name == 'moon':
        scale_factor = 2
    elif name == 'pesawat' :
        scale_factor = 0.8
    elif name == 'rainbow':
        scale_factor = 0.2

    entity = Entity(model=Animation(texture), fps=5, collider='box', scale=(2 * scale_factor, 2 * scale_factor), x=x, y=y, z=-0.45)
    entities[name].append(entity)
    print(f"{name} spawned at ({x}, {y}) with scale {scale_factor}")

position_ex = 5

def spawn_entities():
    global position_ex
    for i in range(100):
        entitas = list(entities.keys())[random.randint(0, len(entities) - 1)]
        position_ex += random.randint(17, 25)
        position_ye = 0
        spawn_entity(entitas, 'assets/' + entitas, position_ex, position_ye)

def start_spawning_entities():
    spawn_entities()

# TABRAKAN DENGAN OBJEK LAIN
def player_collision_check():
    global pemain
    for name, entity_list in entities.items():
        for entity in entity_list:
            if entity.intersects(pemain).hit:
                if name == 'buff':
                    apply_buff()
                    destroy(entity)
                    entity_list.remove(entity)
                    continue

                if not pemain.invincible:
                    game_over()
                    return True
    return False

def enemy_collision_check():
    global pemain, ngejar
    if ngejar and pemain and ngejar.intersects(pemain).hit:
        if not pemain.invincible:
            game_over()
            return True
    return False

# BUFF
def apply_buff():
    global pemain
    pemain.invincible = True
    invoke(remove_buff, delay=7)
    
def remove_buff():
    global pemain
    pemain.invincible = False

# GAME OVER
def game_over():
    global pemain, game_over_text, main_screen_active, score, best_score, music, game_active
    print("Game Over")
    game_over_text = Text(text='Game Over', scale=5, origin=(0, 0), y=0, font='assets/yoster.ttf')
    main_screen_active = False
    game_active = False
    show_game_over_menu()
    
    # CEK DAN UPDATE SCORE TERTINGGI
    if score > best_score:
        best_score = score
        best_score_text.text = f'Best Score: {best_score}'
        save_best_score(best_score)

# MENU GAME OVER
def show_game_over_menu():
    menu_background.visible = True
    quit_button.visible = True

def update():
    global pemain, ngejar, backgrounds, main_screen_active, game_over_text, score, score_time, score_increment_interval, score_speedup

    if pemain and game_active:
       
        # GERAKAN PEMAIN
        pemain.x += held_keys['d'] * 6 * time.dt
        pemain.y += held_keys['w'] * 6 * time.dt

        # GERAKAN LOMPAT PEMAIN
        if held_keys['space']:
            pemain.jump()

        # Update player vertical position and apply gravity
        pemain.y += pemain.velocity_y * time.dt
        pemain.velocity_y -= 9.8 * time.dt

        # Check if player is below a certain height, reset to ground level
        if pemain.y < 0:
            pemain.y = 0
            pemain.velocity_y = 0
            pemain.grounded = True
            pemain.jump_count = 0
            pemain.land()

        # CAMERA NGIKUTIN PEMAIN
        camera.position = (pemain.x, pemain.y, camera.z)
        
        # CEK TABRAKAN PLAYER DENGAN OBJEK LAIN
        if player_collision_check():
            print("Collision detected with an entity")

        # CEK TABRAKAN MUSUH DENGAN OBJEK LAIN
        if enemy_collision_check():
            print("Collision detected with the enemy")

        # SCORE NAMBAH TERUS
        score_time += time.dt
        if score_time >= score_increment_interval:
            score += 1
            score_text.text = f'Score: {score}'
            score_time -= score_increment_interval
            score_increment_interval -= score_speedup

    if ngejar:
        # MUSUH NGEJAR SI PEMAIN
        if held_keys['d']:
            if ngejar.x < (pemain.x - 5) or not pemain.invincible:
                ngejar.x += random.randint(5, 6) * time.dt
        else:
            if ngejar.x < (pemain.x - 5) or not pemain.invincible:
                ngejar.x += random.randint(2, 4) * time.dt

    # Entities movement to the left
    if main_screen_active:
        for name, entity_list in entities.items():
            for entity in entity_list:
                entity.x -= 2 * time.dt
                if entity.x < -10:
                    destroy(entity)
                    entity_list.remove(entity)
                if name == 'moon':  
                    entity.y = 3 * math.sin(time.time() * 3)  
                if name == 'pesawat':  
                    entity.x += 5 * math.sin(time.time() * 3) * time.dt  

        # BACKGROUND SCROLL
        if backgrounds:
            for bg in backgrounds:
                bg.x -= 2 * time.dt
                if bg.x < -96:
                    bg.x += 384

# KELUAR GAME SECARA PAKSA
def input(key):
    if key == 'escape':
        exit()

# NAMPILIN MENU DI LOAD SCREEN
def show_menu(): 
    global game_active
    game_active = False
    menu_background.visible = True
    start_button.visible = True
    quit_button.visible = True

# NGILANGIN MENU SAAT GAME AKTIF
def hide_menu():
    global game_active
    game_active = True
    menu_background.visible = False
    start_button.visible = False
    quit_button.visible = False

# GAME DIMULAI
def start_game():
    hide_menu()
    show_main_screen()
    start_spawning_entities()

# NYIMPEN SCORE TERTINGGI DALAM BENTUK FILE
def save_best_score(score):
    with open('best_score.txt', 'w') as file:
        file.write(str(score))

# 
def load_best_score():
    if os.path.exists('best_score.txt'):
        with open('best_score.txt', 'r') as file:
            return int(file.read())
    return 0

# NAMPILIN SCORE TERTINGGI NYA
best_score = load_best_score()
best_score_text.text = f'Best Score: {best_score}'

show_menu()
app.run()