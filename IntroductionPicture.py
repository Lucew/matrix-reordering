import random

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
import matplotlib.patches

SAVE = False

# use pgf backed
if SAVE:
    matplotlib.use("pgf")
    matplotlib.rcParams.update({
        "pgf.texsystem": "pdflatex",
        'font.family': 'serif',
        'text.usetex': True,
        'pgf.rcfonts': False,
    })


def create_block_matrix(size, inner_value, outer_value):
    matrix = np.zeros((size, size))
    block_size = size // 8  # Divide matrix into four blocks
    outer_block_size = size // 2  # Larger block containing two inner blocks

    for i in range(8):
        row_start = i * block_size
        col_start = i * block_size

        # Create the inner blocks with lower values
        matrix[row_start:row_start + block_size, col_start:col_start + block_size] = inner_value

        # Create the larger outer blocks with even lower values
        row_outer_start = (i // 2) * outer_block_size
        col_outer_start = (i // 2) * outer_block_size
        matrix[row_outer_start:row_outer_start + outer_block_size,
        col_outer_start:col_outer_start + outer_block_size] += outer_value
    matrix[matrix == 0] = np.nan
    return matrix


size = 32  # Size of the matrix
inner_value = 5  # Higher value for inner blocks
outer_value = 2  # Lower value for outer blocks

matrix = create_block_matrix(size, inner_value, outer_value)

# Plot the matrices
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17, 5))
axes = [ax1, ax2]
order = list(range(matrix.shape[0]))
random.Random(42).shuffle(order)
# , cmap=sns.color_palette("light:b", as_cmap=True)
sns.heatmap(matrix[order,:][:, order], ax=ax1, cmap=sns.color_palette("ch:start=.2,rot=-.3", as_cmap=True), cbar=False)
sns.heatmap(matrix, ax=ax2, cmap=sns.color_palette("ch:start=.2,rot=-.3", as_cmap=True), cbar=False)

# add an arrow between the subplots
# Add line from one subplot to the other
xyA = (matrix.shape[0]+1, matrix.shape[0]/2)
xyB = (-1, matrix.shape[0]/2)
# ConnectionPatch handles the transform internally so no need to get fig.transFigure
arrow = matplotlib.patches.ConnectionPatch(
    xyA,
    xyB,
    coordsA=ax1.transData,
    coordsB=ax2.transData,
    # Default shrink parameter is 0 so can be omitted
    color="black",
    arrowstyle="-|>",  # "normal" arrow
    mutation_scale=30,  # controls arrow head size
    linewidth=3,
)
fig.patches.append(arrow)
fig.text(0.5, 0.5, 'Reordering', size=40, horizontalalignment='center', verticalalignment='bottom')

# change the ax layout
for ax in axes:
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])
    ax.axhline(y=0, color='k',linewidth=5)
    ax.axhline(y=matrix.shape[1], color='k',linewidth=5)
    ax.axvline(x=0, color='k',linewidth=5)
    ax.axvline(x=matrix.shape[0], color='k',linewidth=5)
plt.tight_layout()
plt.subplots_adjust(wspace=2)
if SAVE:
    plt.savefig('matrix-reordering.pgf')
else:
    plt.show()