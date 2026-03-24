import pygame
import random
import sys
"""
Cria o Terreno: Usa o algoritmo de autómatos celulares para gerar as grutas.
Define a Missão: Traça um caminho amarelo (via BFS) entre a Costa (Shore) e o Interior (Ruins).
Verifica Barreiras: Coloca um Portão (Gate) no meio do caminho. Se o jogador não tiver as perícias necessárias, o sistema entra em modo de "Reparação".
Repara a Progressão: Utiliza a sua lógica recursiva para descobrir que, para passar o portão, precisas de Basic Weaponry antes de Combat Mastery.
Gera Conteúdo Adaptativo: O código escolhe automaticamente coordenadas no mapa para spawnar o "Wrecked Ship" e a "Old Fortress" antes do portão, para que o jogador possa progredir.
"""
# ----------------------------
# CONFIGURAÇÃO GERAL
# ----------------------------
WIDTH, HEIGHT = 1100, 800  # Espaço extra para a Sidebar
SIDEBAR_WIDTH = 300
CELL_SIZE = 16
COLS, ROWS = (WIDTH - SIDEBAR_WIDTH) // CELL_SIZE, HEIGHT // CELL_SIZE
WALL_PROBABILITY = 0.45
ITERATIONS = 4
TILE_SIZE = 2 * CELL_SIZE # Nodes do Grafo cobrem 2x2 células

# ----------------------------
# 1. THE PROGRESSION GRAPH (Sua Lógica Original)
# ----------------------------
class ProgressionGraph:
    def __init__(self, current_skills):
        self.player_skills = current_skills
        # Dependências explícitas: Skill -> Pré-requisito
        self.dependencies = {
            "Combat_Mastery": "Basic_Weaponry",
            "Deep_Inland_Stamina": "Base_Fitness",
            "Elite_Combat": "Combat_Mastery"
        }
        # Nomes dos locais para spawnar no mapa
        self.unlock_locations = {
            "Basic_Weaponry": "WRECKED_SHIP",
            "Base_Fitness": "TRAINING_GLADE",
            "Combat_Mastery": "OLD_FORTRESS",
            "Deep_Inland_Stamina": "COASTAL_SPRINGS",
            "Elite_Combat": "HERMIT_HUT"
        }

    def can_pass(self, skill):
        return skill in self.player_skills

    def get_required_path(self, target_node):
        """Recursivamente encontra as skills que faltam """
        path_to_unlock = []
        current = target_node
        
        while current in self.dependencies:
            pre_req = self.dependencies[current]
            if pre_req not in self.player_skills:
                path_to_unlock.append(pre_req)
                current = pre_req
            else:
                break
        
        return list(reversed(path_to_unlock))

# ----------------------------
# 2. CLASSES ESPACIAIS E MISSÃO
# ----------------------------
#A Classe Node: 
#Em vez de lidar com milhares de pixels, o computador lida com "Tiles" (nós).
#Propriedade walkable: Determinada pela densidade de paredes.
# Se um 2x2 tiver mais de 90% de parede, o nó é bloqueado.
#Propriedade tag: É aqui que a Missão escreve no Mapa. 
# Quando o gerador decide que um ponto é o "Wrecked Ship", 
# ele atribui essa string ao nó. 
# O motor de renderização depois apenas lê: 
# if node.tag: draw_icon().
class Node:
    def __init__(self, x, y, walkable):
        self.x, self.y = x, y
        self.walkable = walkable
        self.neighbors = []
        self.tag = None  # Armazena o nome do local (ex: "OLD_FORTRESS")

#A Classe MissionDirector: 
# É o "manager" da sessão. 
# Ela guarda o caminho principal (main_path) para que não tenhamos de o recalcular 
# a cada frame, e mantém uma lista de training_nodes para saber onde injetar os itens
#  de reparação.
 #Skill em falta: Basic_Weaponry -> Training Node Tag: "WRECKED_SHIP"
       
class MissionDirector:
    def __init__(self):
        self.main_path = [] #caminho principal (main_path) 
        self.training_nodes = [] #lista de nós para saber onde injetar os itens de reparação.
        self.gate_node = None
        self.gate_skill = "Combat_Mastery" # O obstáculo Inland
        self.missing_skills = []

# ----------------------------
# 3. GERAÇÃO DA GRUTA (Cellular Automata)
# ----------------------------
#Ruído Inicial: Preenchemos a grelha com 1s (paredes) e 0s (chão) aleatoriamente. 
# Com WALL_PROBABILITY = 0.45, o mapa começa muito sujo.
#Simulação de Vizinhos (Smoothing):
#Para cada célula, contamos os 8 vizinhos.
#A Regra da Sobrevivência: Se uma célula está rodeada por muitas paredes (>4), 
# ela torna-se parede. Se está isolada, torna-se chão.
#Iterações: Fazemos isto 4 vezes. 
# Na primeira, removemos o "ruído". 
# Na quarta, as cavernas tornam-se largas e os corredores definidos.
def generate_cave():
    grid = [[1 if random.random() < WALL_PROBABILITY else 0 for _ in range(ROWS)] for _ in range(COLS)]
    for _ in range(ITERATIONS):
        new_grid = [[0 for _ in range(ROWS)] for _ in range(COLS)]
        for x in range(COLS):
            for y in range(ROWS):
                walls = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if nx < 0 or ny < 0 or nx >= COLS or ny >= ROWS or grid[nx][ny] == 1:
                            walls += 1
                new_grid[x][y] = 1 if walls > 4 else 0
        grid = new_grid
    return grid

# ----------------------------
# 4. PATHFINDING (BFS)
# ----------------------------
#BFS (Breadth-First Search):
#Para garantir que o jogador consegue chegar ao fim
#Exploração por Camadas: O BFS começa no ponto Start 
# e visita todos os vizinhos imediatos, depois os vizinhos dos vizinhos, 
# e assim por diante.
#Garantia de Caminho Curto: Ao contrário de outros algoritmos, 
# o BFS garante encontrar o caminho com menos nós entre a Costa e as Ruínas.
#Deteção de Mapas Inválidos: Se o BFS terminar e não encontrar o End, 
# o código deteta que a gruta é impossível (ponto isolado por paredes) 
# e reinicia a geração automaticamente (return run_simulation()).
def find_path(start, end):
    queue = [(start, [start])]
    visited = {start}
    while queue:
        (curr, path) = queue.pop(0)
        if curr == end: return path
        for n in curr.neighbors:
            if n.walkable and n not in visited:
                visited.add(n)
                queue.append((n, path + [n]))
    return []

# ----------------------------
# 5. INTEGRAÇÃO TOTAL (Missão + Progressão)
# ----------------------------
#a Lógica de Progressão altera a Geografia.
#Seleção de Start/End: O código divide o mapa em quadrantes. 
# O Start é forçado a aparecer no primeiro quarto (esquerda) 
# e o End no último (direita), garantindo uma travessia longa.
#
#Injeção do Portão (Gate): O "Director" escolhe o nó central do caminho calculado. 
# Ele "carimba" esse nodo como um obstáculo que exige Combat_Mastery.
#
#O Processo de Reparação (Recursivo):
#O Diretor pergunta ao ProgressionGraph: "O jogador pode passar?"
#Se não, ele corre o get_required_path. 
# Se faltar Basic_Weaponry e Combat_Mastery, ele recebe essa lista.
#
#Spawn Estratégico:
#O código olha apenas para a fatia do caminho antes do portão (main_path[:gate_idx]).
#Ele escolhe nós vizinhos a esse caminho para colocar os itens. 
# Isto cria exploração lateral: o jogador segue o caminho amarelo, 
# vê um desvio azul (o item), recolhe-o e volta ao caminho principal para abrir o portão.
def run_simulation():
    grid = generate_cave()
    nodes = {}
    
    # Criar Grafo de Tiles (2x2)
    for tx in range(COLS // 2):
        for ty in range(ROWS // 2):
            walls = sum(grid[tx*2+cx][ty*2+cy] for cx in range(2) for cy in range(2))
            nodes[(tx, ty)] = Node(tx, ty, walls < 2) # Walkable se houver pouco muro
    
    # Conectar Vizinhos
    for (tx, ty), node in nodes.items():
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            if (tx+dx, ty+dy) in nodes:
                node.neighbors.append(nodes[(tx+dx, ty+dy)])

    # Estado Inicial do Jogador
    prog = ProgressionGraph(current_skills=["Base_Fitness"])
    director = MissionDirector()
    walkable = [n for n in nodes.values() if n.walkable]
    
    if len(walkable) < 20: return run_simulation() # Reinicia se a gruta for minúscula

    # Definir Início e Fim
    start_n = random.choice(walkable[:len(walkable)//4])
    end_n = random.choice(walkable[len(walkable)//2:])
    director.main_path = find_path(start_n, end_n)

    # Aplicar Lógica de Gating (O Portão Inland)
    if len(director.main_path) > 10:
        gate_idx = len(director.main_path) // 2
        director.gate_node = director.main_path[gate_idx]
        
        if not prog.can_pass(director.gate_skill):
            # Encontrar o que falta para desbloquear a habilidade necessária
            # O diretor agora tem uma lista de habilidades em falta  
            # para o jogador adquirir
            director.missing_skills = prog.get_required_path(director.gate_skill) + [director.gate_skill]
            
            # Spawnar os locais de treino no mapa ANTES do portão
            pre_gate_segment = director.main_path[:gate_idx]
            for skill in director.missing_skills:
                if pre_gate_segment:
                    # Escolhe um nó perto do caminho mas não NO caminho
                    pivot = random.choice(pre_gate_segment)
                    for n in pivot.neighbors:
                        if n.walkable and n not in director.main_path:
                            n.tag = prog.unlock_locations[skill]
                            director.training_nodes.append(n)
                            break

    return grid, nodes, director, prog, start_n, end_n

# ----------------------------
# 6. VISUALIZAÇÃO (Pygame)
# ----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Island PCG: Mission & Progression")
font = pygame.font.SysFont("Courier New", 14, bold=True)
title_font = pygame.font.SysFont("Courier New", 18, bold=True)


def draw_screen(grid, nodes, director, prog, start, end):
    screen.fill((25, 25, 30))
    
    # Desenhar Células (Cave)
    for x in range(COLS):
        for y in range(ROWS):
            color = (40, 40, 45) if grid[x][y] else (160, 160, 170)
            pygame.draw.rect(screen, color, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Desenhar Caminho da Missão (Amarelo)
    if director.main_path:
        pts = [(n.x*TILE_SIZE + TILE_SIZE//2, n.y*TILE_SIZE + TILE_SIZE//2) for n in director.main_path]
        pygame.draw.lines(screen, (255, 215, 0), False, pts, 4)

    # Desenhar Elementos do Grafo
    for node in nodes.values():
        pos = (node.x*TILE_SIZE + TILE_SIZE//2, node.y*TILE_SIZE + TILE_SIZE//2)
        
        if node == start:
            pygame.draw.circle(screen, (0, 255, 0), pos, 10)
            screen.blit(font.render("SHORE", True, (0, 255, 0)), (pos[0]-20, pos[1]-25))
        elif node == end:
            pygame.draw.circle(screen, (255, 0, 0), pos, 10)
            screen.blit(font.render("RUINS", True, (255, 0, 0)), (pos[0]-20, pos[1]-25))
        elif node == director.gate_node:
            pygame.draw.rect(screen, (255, 100, 0), (pos[0]-10, pos[1]-10, 20, 20))
            screen.blit(font.render("GATE", True, (255, 100, 0)), (pos[0]-15, pos[1]-28))
        elif node.tag:
            pygame.draw.rect(screen, (0, 180, 255), (pos[0]-8, pos[1]-8, 16, 16))
            screen.blit(font.render(node.tag, True, (0, 200, 255)), (pos[0]+12, pos[1]-8))

    # SIDEBAR UI
    ui_x = WIDTH - SIDEBAR_WIDTH
    pygame.draw.rect(screen, (10, 10, 15), (ui_x, 0, SIDEBAR_WIDTH, HEIGHT))
    pygame.draw.line(screen, (100, 100, 100), (ui_x, 0), (ui_x, HEIGHT), 2)
    
    y = 30
    screen.blit(title_font.render("--- MISSION LOG ---", True, (255, 255, 255)), (ui_x+20, y))
    y += 40
    
    status_txt = "LOCKED" if director.missing_skills else "CLEAR"
    status_col = (255, 100, 0) if director.missing_skills else (0, 255, 0)
    screen.blit(font.render(f"INLAND GATE: {status_txt}", True, status_col), (ui_x+20, y))
    
    if director.missing_skills:
        y += 40
        screen.blit(font.render("REPAIR PATH DETECTED:", True, (0, 200, 255)), (ui_x+20, y))
        for skill in director.missing_skills:
            y += 25
            loc = prog.unlock_locations[skill]
            screen.blit(font.render(f"> Find {loc}", True, (0, 150, 255)), (ui_x+30, y))

    screen.blit(font.render("[SPACE] REGENERATE ISLAND", True, (100, 255, 100)), (ui_x+20, HEIGHT - 40))

# ----------------------------
# LOOP PRINCIPAL
# ----------------------------
def main():
    grid, nodes, director, prog, sn, en = run_simulation()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    grid, nodes, director, prog, sn, en = run_simulation()

        draw_screen(grid, nodes, director, prog, sn, en)
        pygame.display.flip()

if __name__ == "__main__":
    main()