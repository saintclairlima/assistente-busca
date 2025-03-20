import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Load JSON
with open('api/testes/resultados/ollama/ollama.json', 'r', encoding='utf-8') as arq:
    c = json.load(arq)

# Initialize dictionaries
llma = {"load_duration": [], "prompt_eval_duration": [], "eval_duration": [], "total_duration": []}
dpsk = {"load_duration": [], "prompt_eval_duration": [], "eval_duration": [], "total_duration": []}

dicionario = {
    "total_duration": "duração total",
    "load_duration": "carregamento",
    "prompt_eval_duration": "processamento do prompt",
    "eval_duration": "geração da resposta"
}

# Extract durations
for item in c:
    respeita_limiar = True
    for metrica in ["total_duration", "load_duration", "prompt_eval_duration", "eval_duration"]:
        if metrica in item["resposta_deepseek-r1:latest"] and metrica in item["resposta_llama3.1"]:
            if item["resposta_deepseek-r1:latest"][metrica] / 1e9 > 50 or item["resposta_llama3.1"][metrica] / 1e9 > 50:
                respeita_limiar = False
                break
    if 'total_duration' in item["resposta_deepseek-r1:latest"] and respeita_limiar:
        try:
            for metrica in llma.keys():
                dpsk[metrica].append(item["resposta_deepseek-r1:latest"][metrica] / 1e9)
                llma[metrica].append(item["resposta_llama3.1"][metrica] / 1e9)
        except:
            continue

# Define per-model colors
model_colors = {
    "llma": "#aec7e8",   # light blue
    "dpsk": "#ffbb78"    # light orange
}

fig, ax = plt.subplots(figsize=(6, 6))

box_data = [llma["total_duration"], dpsk["total_duration"]]
box_labels = ['llama3.1', 'deepseek-r1']
box_colors = [model_colors["llma"], model_colors["dpsk"]]

# Create boxplot
bp = ax.boxplot(box_data, patch_artist=True, labels=box_labels)

# Apply pastel colors
for patch, color in zip(bp['boxes'], box_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

# Styling
ax.set_title(f'Tempo de execução total', fontsize=14)
ax.set_ylabel("Tempo (s)")
ax.grid(True, axis='y', linestyle='--', linewidth=0.5, alpha=0.6)

plt.tight_layout()
plt.show()

# Summary statistics
df_llma = pd.DataFrame(llma)
df_dpsk = pd.DataFrame(dpsk)

statistics = ['mean', 'std', 'median', 'min', 'max']
summary_llma = df_llma.agg(statistics).rename_axis('Statistic')
summary_dpsk = df_dpsk.agg(statistics).rename_axis('Statistic')

comparison = pd.concat({'llma': summary_llma, 'dpsk': summary_dpsk}, axis=1).round(3)
print(comparison)


# ==================================

# import matplotlib.pyplot as plt
# import numpy as np

# # New data
# stats = ['mínimo', 'média', 'mediana', 'máximo']
# llma_response = [0.205, 2.623, 1.908, 19.451]
# dpsk_response = [2.06, 12.999, 12.222, 47.238]
# llma_total = [0.502, 3.361, 2.651, 20.203]
# dpsk_total = [2.527, 13.721, 12.945, 47.922]

# # Settings
# bar_width = 0.35
# x = np.arange(len(stats))

# # Color palette (same pastel tones)
# model_colors = {
#     "llma": "#aec7e8",   # light blue
#     "dpsk": "#ffbb78"    # light orange
# }

# # Create subplots
# fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

# # --- Subplot 1: Geração da Resposta ---
# axes[0].bar(x - bar_width/2, llma_response, width=bar_width, color=model_colors["llma"], label='llama3.1')
# axes[0].bar(x + bar_width/2, dpsk_response, width=bar_width, color=model_colors["dpsk"], label='deepseek-r1')

# axes[0].set_title("Tempo de Geração da Resposta")
# axes[0].set_xticks(x)
# axes[0].set_xticklabels(stats)
# axes[0].set_ylabel("Tempo (s)")
# axes[0].grid(True, axis='y', linestyle='--', linewidth=0.5, alpha=0.6)
# axes[0].legend()

# # --- Subplot 2: Tempo Total ---
# axes[1].bar(x - bar_width/2, llma_total, width=bar_width, color=model_colors["llma"], label='llama3.1')
# axes[1].bar(x + bar_width/2, dpsk_total, width=bar_width, color=model_colors["dpsk"], label='deepseek-r1')

# axes[1].set_title("Tempo Total")
# axes[1].set_xticks(x)
# axes[1].set_xticklabels(stats)
# axes[1].grid(True, axis='y', linestyle='--', linewidth=0.5, alpha=0.6)
# axes[1].legend()

# # Global title
# fig.suptitle("Tempo de Execução", fontsize=16)

# plt.tight_layout(rect=[0, 0, 1, 0.95])
# plt.show()
