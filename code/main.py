import pygame, sys
import json
import os
from player import Player
import obstacle
from alien import Alien, Extra
from random import choice, randint
from laser import Laser
 
class Game:
	def __init__(self):
		# Player setup
		player_sprite = Player((screen_width / 2,screen_height),screen_width,5)
		self.player = pygame.sprite.GroupSingle(player_sprite)

		# health and score setup
		self.lives = 3
		self.live_surf = pygame.image.load('../graphics/player.png').convert_alpha()
		self.live_x_start_pos = screen_width - (self.live_surf.get_size()[0] * 2 + 20)
		self.score = 0
		self.font = pygame.font.Font('../font/Pixeled.ttf',20)
		
		# Highscore setup
		self.highscore_file = 'highscore.json'
		self.highscore_data = self.load_highscore()
		self.highscore = self.highscore_data.get('score', 0)
		self.highscore_player = self.highscore_data.get('player', 'Anonymous')
		self.game_over = False
		self.new_highscore = False
		self.entering_name = False
		self.player_name = ""
		self.name_input_active = False

		# Obstacle setup
		self.shape = obstacle.shape
		self.block_size = 6
		self.blocks = pygame.sprite.Group()
		self.obstacle_amount = 4
		self.obstacle_x_positions = [num * (screen_width / self.obstacle_amount) for num in range(self.obstacle_amount)]
		self.create_multiple_obstacles(*self.obstacle_x_positions, x_start = screen_width / 15, y_start = 480)

		# Level setup
		self.level = 1
		self.max_level = 10
		self.level_complete = False
		self.level_transition_timer = 0
		self.level_transition_duration = 180  # 3 seconds at 60 FPS

		# Alien setup
		self.aliens = pygame.sprite.Group()
		self.alien_lasers = pygame.sprite.Group()
		self.alien_setup()
		self.alien_direction = 1

		# Extra setup
		self.extra = pygame.sprite.GroupSingle()
		self.extra_spawn_time = randint(40,80)

		# Audio
		music = pygame.mixer.Sound('../audio/music.wav')
		music.set_volume(0.2)
		music.play(loops = -1)
		self.laser_sound = pygame.mixer.Sound('../audio/laser.wav')
		self.laser_sound.set_volume(0.5)
		self.explosion_sound = pygame.mixer.Sound('../audio/explosion.wav')
		self.explosion_sound.set_volume(0.3)

	def load_highscore(self):
		"""Load highscore from JSON file"""
		try:
			if os.path.exists(self.highscore_file):
				with open(self.highscore_file, 'r') as f:
					data = json.load(f)
					return {
						'score': data.get('score', 0),
						'player': data.get('player', 'Anonymous')
					}
			else:
				return {'score': 0, 'player': 'Anonymous'}
		except (json.JSONDecodeError, IOError):
			return {'score': 0, 'player': 'Anonymous'}

	def save_highscore(self, player_name):
		"""Save highscore to JSON file"""
		try:
			data = {
				'score': self.highscore,
				'player': player_name
			}
			with open(self.highscore_file, 'w') as f:
				json.dump(data, f, indent=2)
		except IOError:
			print("Error saving highscore file")

	def check_new_highscore(self):
		"""Check if current score is a new highscore"""
		if self.score > self.highscore:
			self.new_highscore = True
			self.entering_name = True
			self.name_input_active = True
			self.player_name = ""
			return True
		return False

	def submit_highscore(self):
		"""Submit the new highscore with player name"""
		if self.player_name.strip() == "":
			self.player_name = "Anonymous"
		
		self.highscore = self.score
		self.highscore_player = self.player_name
		self.save_highscore(self.player_name)
		self.entering_name = False
		self.name_input_active = False

	def handle_name_input(self, event):
		"""Handle keyboard input for player name"""
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RETURN:
				self.submit_highscore()
			elif event.key == pygame.K_BACKSPACE:
				self.player_name = self.player_name[:-1]
			else:
				# Only allow alphanumeric characters and spaces, max length 15
				if len(self.player_name) < 15 and (event.unicode.isalnum() or event.unicode == ' '):
					self.player_name += event.unicode

	def create_obstacle(self, x_start, y_start,offset_x):
		for row_index, row in enumerate(self.shape):
			for col_index,col in enumerate(row):
				if col == 'x':
					x = x_start + col_index * self.block_size + offset_x
					y = y_start + row_index * self.block_size
					block = obstacle.Block(self.block_size,(241,79,80),x,y)
					self.blocks.add(block)

	def create_multiple_obstacles(self,*offset,x_start,y_start):
		for offset_x in offset:
			self.create_obstacle(x_start,y_start,offset_x)

	def alien_setup(self):
		"""Setup aliens based on current level"""
		# Base configuration
		base_rows = 6
		base_cols = 8
		x_distance = 60
		y_distance = 48
		x_offset = 70
		y_offset = 100
		
		# Level-based modifications
		rows = min(base_rows + (self.level - 1) // 2, 8)  # Increase rows every 2 levels, max 8
		cols = min(base_cols + (self.level - 1) // 3, 10)  # Increase cols every 3 levels, max 10
		
		# Adjust spacing for higher levels
		if self.level > 5:
			x_distance = max(50, 60 - (self.level - 5) * 2)
			y_distance = max(40, 48 - (self.level - 5) * 2)
		
		# Adjust starting position based on number of columns
		x_offset = max(20, (screen_width - (cols * x_distance)) // 2)
		
		for row_index in range(rows):
			for col_index in range(cols):
				x = col_index * x_distance + x_offset
				y = row_index * y_distance + y_offset
				
				# Color distribution based on level
				if self.level <= 3:
					if row_index == 0: alien_sprite = Alien('yellow',x,y)
					elif 1 <= row_index <= 2: alien_sprite = Alien('green',x,y)
					else: alien_sprite = Alien('red',x,y)
				elif self.level <= 6:
					if row_index <= 1: alien_sprite = Alien('yellow',x,y)
					elif 2 <= row_index <= 3: alien_sprite = Alien('green',x,y)
					else: alien_sprite = Alien('red',x,y)
				else:
					# Higher levels have more yellow (high value) aliens
					if row_index <= 2: alien_sprite = Alien('yellow',x,y)
					elif 3 <= row_index <= 4: alien_sprite = Alien('green',x,y)
					else: alien_sprite = Alien('red',x,y)
				
				self.aliens.add(alien_sprite)

	def get_alien_speed(self):
		"""Get alien movement speed based on level"""
		return min(1 + (self.level - 1) * 0.3, 4)  # Increase speed each level, max 4

	def get_alien_shoot_frequency(self):
		"""Get alien shooting frequency based on level"""
		base_frequency = 800
		return max(200, base_frequency - (self.level - 1) * 50)  # Faster shooting each level

	def get_extra_spawn_frequency(self):
		"""Get extra alien spawn frequency based on level"""
		return randint(max(200, 600 - self.level * 30), max(400, 800 - self.level * 20))

	def alien_position_checker(self):
		all_aliens = self.aliens.sprites()
		for alien in all_aliens:
			if alien.rect.right >= screen_width:
				self.alien_direction = -1
				self.alien_move_down(2)
			elif alien.rect.left <= 0:
				self.alien_direction = 1
				self.alien_move_down(2)

	def alien_move_down(self,distance):
		if self.aliens:
			# Level-based move down distance
			level_distance = distance + (self.level - 1) * 0.5
			for alien in self.aliens.sprites():
				alien.rect.y += level_distance

	def alien_shoot(self):
		if self.aliens.sprites():
			random_alien = choice(self.aliens.sprites())
			laser_sprite = Laser(random_alien.rect.center,6,screen_height)
			self.alien_lasers.add(laser_sprite)
			self.laser_sound.play()

	def extra_alien_timer(self):
		self.extra_spawn_time -= 1
		if self.extra_spawn_time <= 0:
			self.extra.add(Extra(choice(['right','left']),screen_width))
			self.extra_spawn_time = self.get_extra_spawn_frequency()

	def check_level_complete(self):
		"""Check if level is complete and handle transition"""
		if not self.aliens.sprites() and not self.level_complete:
			self.level_complete = True
			self.level_transition_timer = self.level_transition_duration
			
			# Bonus points for completing level
			level_bonus = self.level * 100
			self.score += level_bonus

	def handle_level_transition(self):
		"""Handle level transition logic"""
		if self.level_complete:
			self.level_transition_timer -= 1
			if self.level_transition_timer <= 0:
				self.next_level()

	def next_level(self):
		"""Advance to next level"""
		if self.level < self.max_level:
			self.level += 1
			self.level_complete = False
			
			# Clear remaining projectiles
			self.alien_lasers.empty()
			self.player.sprite.lasers.empty()
			
			# Restore some obstacles for new level
			self.blocks.empty()
			self.create_multiple_obstacles(*self.obstacle_x_positions, x_start = screen_width / 15, y_start = 480)
			
			# Setup new aliens
			self.alien_setup()
			self.alien_direction = 1
			
			# Reset extra alien timer
			self.extra_spawn_time = self.get_extra_spawn_frequency()
		else:
			# Game completed all levels
			if not self.new_highscore:
				self.check_new_highscore()
			self.game_over = True

	def collision_checks(self):

		# player lasers 
		if self.player.sprite.lasers:
			for laser in self.player.sprite.lasers:
				# obstacle collisions
				if pygame.sprite.spritecollide(laser,self.blocks,True):
					laser.kill()
					

				# alien collisions
				aliens_hit = pygame.sprite.spritecollide(laser,self.aliens,True)
				if aliens_hit:
					for alien in aliens_hit:
						self.score += alien.value
					laser.kill()
					self.explosion_sound.play()

				# extra collision
				if pygame.sprite.spritecollide(laser,self.extra,True):
					self.score += 500
					laser.kill()

		# alien lasers 
		if self.alien_lasers:
			for laser in self.alien_lasers:
				# obstacle collisions
				if pygame.sprite.spritecollide(laser,self.blocks,True):
					laser.kill()

				if pygame.sprite.spritecollide(laser,self.player,False):
					laser.kill()
					self.lives -= 1
					if self.lives <= 0:
						self.game_over = True
						self.check_new_highscore()

		# aliens
		if self.aliens:
			for alien in self.aliens:
				pygame.sprite.spritecollide(alien,self.blocks,True)

				if pygame.sprite.spritecollide(alien,self.player,False):
					self.game_over = True
					self.check_new_highscore()
	
	def display_lives(self):
		for live in range(self.lives - 1):
			x = self.live_x_start_pos + (live * (self.live_surf.get_size()[0] + 10))
			screen.blit(self.live_surf,(x,8))

	def display_score(self):
		score_surf = self.font.render(f'score: {self.score}',False,'white')
		score_rect = score_surf.get_rect(topleft = (10,-10))
		screen.blit(score_surf,score_rect)

	def display_level(self):
		level_surf = self.font.render(f'Level: {self.level}',False,'white')
		level_rect = level_surf.get_rect(topright = (screen_width - 10, -10))
		screen.blit(level_surf,level_rect)

	def display_level_transition(self):
		"""Display level transition screen"""
		if self.level_complete and self.level_transition_timer > 0:
			# Semi-transparent overlay
			overlay = pygame.Surface((screen_width, screen_height))
			overlay.set_alpha(128)
			overlay.fill((0, 0, 0))
			screen.blit(overlay, (0, 0))
			
			if self.level < self.max_level:
				# Level complete message
				complete_surf = self.font.render('LEVEL COMPLETE!',False,'gold')
				complete_rect = complete_surf.get_rect(center = (screen_width / 2, screen_height / 2 - 60))
				screen.blit(complete_surf,complete_rect)
				
				# Level bonus
				bonus_surf = self.font.render(f'Level Bonus: {self.level * 100}',False,'yellow')
				bonus_rect = bonus_surf.get_rect(center = (screen_width / 2, screen_height / 2 - 30))
				screen.blit(bonus_surf,bonus_rect)
				
				# Next level message
				next_surf = self.font.render(f'Preparing Level {self.level + 1}...',False,'white')
				next_rect = next_surf.get_rect(center = (screen_width / 2, screen_height / 2 + 30))
				screen.blit(next_surf,next_rect)
			else:
				# Game completed
				complete_surf = self.font.render('GAME COMPLETED!',False,'gold')
				complete_rect = complete_surf.get_rect(center = (screen_width / 2, screen_height / 2 - 30))
				screen.blit(complete_surf,complete_rect)
				
				congrats_surf = self.font.render('You are a Space Invaders Master!',False,'yellow')
				congrats_rect = congrats_surf.get_rect(center = (screen_width / 2, screen_height / 2 + 30))
				screen.blit(congrats_surf,congrats_rect)

	def display_highscore(self):
		highscore_surf = self.font.render(f'highscore: {self.highscore}',False,'white')
		highscore_rect = highscore_surf.get_rect(topleft = (10,15))
		screen.blit(highscore_surf,highscore_rect)
		
		# Display highscore holder name
		player_surf = self.font.render(f'by: {self.highscore_player}',False,'yellow')
		player_rect = player_surf.get_rect(topleft = (10,40))
		screen.blit(player_surf,player_rect)

	def victory_message(self):
		"""Display victory message for current level"""
		if not self.aliens.sprites() and not self.level_complete:
			victory_surf = self.font.render('Level Clear!',False,'white')
			victory_rect = victory_surf.get_rect(center = (screen_width / 2, screen_height / 2))
			screen.blit(victory_surf,victory_rect)

	def new_highscore_message(self):
		"""Display new highscore message and name input"""
		if self.new_highscore and self.entering_name:
			# New highscore message
			new_highscore_surf = self.font.render('NEW HIGHSCORE!',False,'gold')
			new_highscore_rect = new_highscore_surf.get_rect(center = (screen_width / 2, screen_height / 2 - 60))
			screen.blit(new_highscore_surf,new_highscore_rect)
			
			# Score display
			score_surf = self.font.render(f'Score: {self.score}',False,'white')
			score_rect = score_surf.get_rect(center = (screen_width / 2, screen_height / 2 - 30))
			screen.blit(score_surf,score_rect)
			
			# Name input prompt
			prompt_surf = self.font.render('Enter your name:',False,'white')
			prompt_rect = prompt_surf.get_rect(center = (screen_width / 2, screen_height / 2))
			screen.blit(prompt_surf,prompt_rect)
			
			# Name input box
			name_color = 'yellow' if self.name_input_active else 'gray'
			name_surf = self.font.render(f'{self.player_name}_',False,name_color)
			name_rect = name_surf.get_rect(center = (screen_width / 2, screen_height / 2 + 30))
			screen.blit(name_surf,name_rect)
			
			# Instructions
			instruction_surf = self.font.render('Press ENTER to submit',False,'gray')
			instruction_rect = instruction_surf.get_rect(center = (screen_width / 2, screen_height / 2 + 60))
			screen.blit(instruction_surf,instruction_rect)

	def game_over_message(self):
		if self.game_over and not self.entering_name:
			if self.new_highscore:
				# Show congratulations message
				congrats_surf = self.font.render('CONGRATULATIONS!',False,'gold')
				congrats_rect = congrats_surf.get_rect(center = (screen_width / 2, screen_height / 2 - 30))
				screen.blit(congrats_surf,congrats_rect)
				
				highscore_surf = self.font.render(f'New Highscore: {self.highscore}',False,'yellow')
				highscore_rect = highscore_surf.get_rect(center = (screen_width / 2, screen_height / 2))
				screen.blit(highscore_surf,highscore_rect)
				
				player_surf = self.font.render(f'by {self.highscore_player}',False,'yellow')
				player_rect = player_surf.get_rect(center = (screen_width / 2, screen_height / 2 + 30))
				screen.blit(player_surf,player_rect)
			else:
				game_over_surf = self.font.render('GAME OVER',False,'white')
				game_over_rect = game_over_surf.get_rect(center = (screen_width / 2, screen_height / 2))
				screen.blit(game_over_surf,game_over_rect)
			
			restart_surf = self.font.render('Press R to restart',False,'white')
			restart_rect = restart_surf.get_rect(center = (screen_width / 2, screen_height / 2 + 60))
			screen.blit(restart_surf,restart_rect)

	def restart_game(self):
		"""Reset game state for restart"""
		self.lives = 3
		self.score = 0
		self.level = 1
		self.game_over = False
		self.new_highscore = False
		self.entering_name = False
		self.player_name = ""
		self.name_input_active = False
		self.level_complete = False
		self.level_transition_timer = 0
		
		# Clear all sprite groups
		self.aliens.empty()
		self.alien_lasers.empty()
		self.blocks.empty()
		self.extra.empty()
		self.player.sprite.lasers.empty()
		
		# Reset player position
		self.player.sprite.rect.centerx = screen_width / 2
		
		# Recreate obstacles and aliens
		self.create_multiple_obstacles(*self.obstacle_x_positions, x_start = screen_width / 15, y_start = 480)
		self.alien_setup()
		self.alien_direction = 1
		self.extra_spawn_time = self.get_extra_spawn_frequency()

	def run(self):
		if not self.game_over:
			self.player.update()
			self.alien_lasers.update()
			self.extra.update()
			
			self.aliens.update(self.alien_direction * self.get_alien_speed())
			self.alien_position_checker()
			self.extra_alien_timer()
			self.collision_checks()
			self.check_level_complete()
			self.handle_level_transition()
		
		# Always draw everything
		self.player.sprite.lasers.draw(screen)
		self.player.draw(screen)
		self.blocks.draw(screen)
		self.aliens.draw(screen)
		self.alien_lasers.draw(screen)
		self.extra.draw(screen)
		self.display_lives()
		self.display_score()
		self.display_level()
		self.display_highscore()
		self.victory_message()
		self.display_level_transition()
		self.new_highscore_message()
		self.game_over_message()

class CRT:
	def __init__(self):
		self.tv = pygame.image.load('../graphics/tv.png').convert_alpha()
		self.tv = pygame.transform.scale(self.tv,(screen_width,screen_height))

	def create_crt_lines(self):
		line_height = 3
		line_amount = int(screen_height / line_height)
		for line in range(line_amount):
			y_pos = line * line_height
			pygame.draw.line(self.tv,'black',(0,y_pos),(screen_width,y_pos),1)

	def draw(self):
		self.tv.set_alpha(randint(75,90))
		self.create_crt_lines()
		screen.blit(self.tv,(0,0))

if __name__ == '__main__':
	pygame.init()
	screen_width = 600
	screen_height = 600
	screen = pygame.display.set_mode((screen_width,screen_height))
	clock = pygame.time.Clock()
	game = Game()
	crt = CRT()

	ALIENLASER = pygame.USEREVENT + 1
	pygame.time.set_timer(ALIENLASER,game.get_alien_shoot_frequency())

	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == ALIENLASER and not game.game_over:
				game.alien_shoot()
				# Update alien shooting frequency based on current level
				pygame.time.set_timer(ALIENLASER,game.get_alien_shoot_frequency())
			if event.type == pygame.KEYDOWN:
				if game.entering_name:
					game.handle_name_input(event)
				elif event.key == pygame.K_r and game.game_over:
					game.restart_game()
					# Reset alien shooting frequency
					pygame.time.set_timer(ALIENLASER,game.get_alien_shoot_frequency())

		screen.fill((30,30,30))
		game.run()
		#crt.draw()
			
		pygame.display.flip()
		clock.tick(60)