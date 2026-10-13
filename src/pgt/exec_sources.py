import copy
import csv
from dataclasses import make_dataclass
from decimal import Decimal
from pathlib import Path

from pgt.exec_config import CONFIG

TYPE_MAP = {'str': str, 'int': int, 'float': float, 'Decimal': Decimal}


class OHLCVMixin:
  __slots__ = ()

  @property
  def hl2(self):
    return (self.low + self.high) / 2


class CSVDataSource:
  def __init__(self, source_file: Path):
    self.source_file = source_file
    self.selected_columns = None

  def select(self, *columns):
    new = copy.copy(self)
    new.selected_columns = list(columns)
    return new

  def _generate_row_convertor(self, header):
    schema = CONFIG['CSVDataSource']['schema']
    columns = self.selected_columns or [col for col in header if col in schema]
    indices = [header.index(col) for col in columns]
    types = [TYPE_MAP[schema[col]] for col in columns]

    Row = make_dataclass('Row', zip(columns, types), bases=(OHLCVMixin,), slots=True)

    converted = (f'{t.__name__}(row[{i}])' for i, t in zip(indices, types))
    code = (
      'def row_convertor(row):\n'
      f"  return Row({', '.join(converted)})"
    )

    namespace = {'Row': Row, 'Decimal': Decimal}
    exec(code, namespace)
    self.row_convertor = namespace['row_convertor']
    # print(code)

  def __iter__(self):
    with open(self.source_file, newline='') as f:
      reader = csv.reader(f)
      header = next(reader)
      self._generate_row_convertor(header)
      for row in reader:
        yield self.row_convertor(row)

'''
def row_convertor(row):
  return Row(int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]), int(row[6]), float(row[7]), int(row[8]), float(row[9]), float(row[10]))
'''

class ZipCSVDataSource(CSVDataSource):
  def __iter__(self):
    with open(self.source_file, newline='') as f:
      reader = csv.reader(f)
      header = next(reader)

      schema = CONFIG['CSVDataSource']['schema']
      columns = self.selected_columns or [col for col in header if col in schema]
      indices = [header.index(col) for col in columns]
      types = [TYPE_MAP[schema[col]] for col in columns]

      Row = make_dataclass('Row', zip(columns, types), bases=(OHLCVMixin,), slots=True)

      for row in reader:
        yield Row(*[t(row[i]) for t, i in zip(types, indices)])
