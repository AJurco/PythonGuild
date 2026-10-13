"""Benchmark exec-generated vs zip row conversion.

Run once before the talk (takes a few minutes):
  uv run python -m pgt.exec_timeit

In the notebook, only load the saved results and plot them:
  from pgt.exec_timeit import load, plot
  plot(load())
"""
import contextlib
import io
import timeit
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from pgt.exec_config import CONFIG
from pgt.exec_sources import CSVDataSource, ZipCSVDataSource

ROOT = Path(__file__).parents[2]
RESULTS = ROOT / 'results' / 'exec_timeit.csv'

APPROACHES = {'exec': CSVDataSource, 'zip': ZipCSVDataSource}
COLORS = {'exec': '#2a78d6', 'zip': '#eb6834'}
NUMBERS = ('Decimal', 'float')


@contextlib.contextmanager
def numbers_as(type_name):
  """Temporarily replace every Decimal column in the schema with `type_name`."""
  schema = CONFIG['CSVDataSource']['schema']
  original = dict(schema)
  schema.update({col: type_name for col, t in original.items() if t == 'Decimal'})
  try:
    yield
  finally:
    schema.clear()
    schema.update(original)


def time_pass(src):
  with contextlib.redirect_stdout(io.StringIO()):  # hide the printed generated code
    return timeit.timeit(lambda: deque(src, maxlen=0), number=1)


def run(file, runs=50):
  # Interleave: every round times all four combinations once, so a slow period
  # (throttling, background load) affects all of them equally.
  records = []
  for i in range(runs):
    print(f'round {i + 1}/{runs}', end='\r', flush=True)
    for numbers in NUMBERS:
      with numbers_as(numbers):
        for approach, cls in APPROACHES.items():
          records.append({'numbers': numbers, 'approach': approach, 'seconds': time_pass(cls(file))})
  print()
  df = pd.DataFrame(records)
  print(df.groupby(['numbers', 'approach'])['seconds'].median().round(3))
  return df


def load(path=RESULTS):
  return pd.read_csv(path)


def plot(df):
  sns.set_theme(style='whitegrid', font_scale=1.3)
  fig, axes = plt.subplots(1, 2, figsize=(16, 9), sharey=True, layout='constrained')

  for ax, numbers in zip(axes, NUMBERS):
    data = df[df['numbers'] == numbers]
    medians = data.groupby('approach')['seconds'].median()

    sns.barplot(
      data=data, x='approach', y='seconds', hue='approach', estimator='median',
      order=list(APPROACHES), palette=COLORS, saturation=1, errorbar=None, width=0.5, legend=False, ax=ax,
    )
    for container in ax.containers:
      ax.bar_label(container, fmt='%.3f s', padding=4)

    ratio = medians['exec'] / medians['zip']
    ax.set_title(f'{numbers}\nexec takes {ratio:.0%} of zip time')
    ax.set_xlabel('')
    ax.set_ylabel('seconds per pass' if ax is axes[0] else '')
    ax.margins(y=0.15)
    ax.grid(axis='x', visible=False)

  runs = df.groupby(['numbers', 'approach']).size().min()
  fig.suptitle(f'Row conversion: exec-generated vs zip (median of {runs} runs)', fontsize=20)
  sns.despine(fig)
  return fig


if __name__ == '__main__':
  file = next((ROOT / 'data').glob('*.csv'))
  df = run(file)
  RESULTS.parent.mkdir(exist_ok=True)
  df.to_csv(RESULTS, index=False)
  plot(df).savefig(RESULTS.with_suffix('.png'), dpi=150)
  print(f'Saved {RESULTS} and {RESULTS.with_suffix(".png")}')
