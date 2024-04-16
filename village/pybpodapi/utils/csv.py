import csv as csv

csv.field_size_limit(10000000)

CSV_DELIMITER = ";"
CSV_QUOTECHAR = "|"
CSV_QUOTING = csv.QUOTE_MINIMAL
CSV_LINETERMINATOR = "\n"


class Writer(object):

    def __init__(self, filestream, columns_headers=None):
        self.filestream = filestream
        self.csvwriter = csv.writer(
            filestream,
            delimiter=CSV_DELIMITER,
            quotechar=CSV_QUOTECHAR,
            quoting=CSV_QUOTING,
            lineterminator=CSV_LINETERMINATOR,
        )
        self.columns_headers = columns_headers

        self._write_header = True if columns_headers else False

    def writerow(self, row):
        if self._write_header:
            self.csvwriter.writerow(self.columns_headers)
            self._write_header = False

        self.csvwriter.writerow(row)

    def flush(self):
        self.filestream.flush()


class Reader(object):

    def __init__(self, filestream):
        self.csvreader = csv.reader(
            filestream,
            delimiter=CSV_DELIMITER,
            quotechar=CSV_QUOTECHAR,
            quoting=CSV_QUOTING,
            lineterminator=CSV_LINETERMINATOR,
        )

    def __iter__(self):
        return self

    def __next__(self):
        row = next(self.csvreader, None)

        if row is None:
            raise StopIteration

        return row
