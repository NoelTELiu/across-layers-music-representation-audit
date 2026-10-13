"""Fetch metadata and ONE official MAESTRO MIDI through ZIP HTTP ranges."""
import io
import json
import re
import zipfile
from pathlib import Path
import requests
from .common import ROOT, load_config, sha256, write_json


class HTTPRangeReader(io.RawIOBase):
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()
        self.position = 0
        self.bytes_received = 0
        r = self.session.get(url, headers={'Range': 'bytes=0-0', 'Accept-Encoding': 'identity'}, timeout=60, stream=True)
        r.raise_for_status()
        if r.status_code != 206:
            raise RuntimeError('Server does not support byte ranges; refusing full archive download.')
        match = re.fullmatch(r'bytes 0-0/(\d+)', r.headers.get('Content-Range', ''))
        if not match:
            raise RuntimeError('Invalid HTTP Content-Range')
        self.size = int(match.group(1))
        self.etag = r.headers.get('ETag')
        self.bytes_received += len(r.content)

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else (self.position if whence == 1 else self.size) + offset
        if self.position < 0:
            raise ValueError('Negative seek')
        return self.position

    def read(self, size=-1):
        end = self.size if size < 0 else min(self.size, self.position + size)
        if end <= self.position:
            return b''
        headers = {'Range': f'bytes={self.position}-{end-1}', 'Accept-Encoding': 'identity'}
        if self.etag:
            headers['If-Match'] = self.etag
        r = self.session.get(self.url, headers=headers, timeout=60, stream=True)
        r.raise_for_status()
        expected = f'bytes {self.position}-{end-1}/{self.size}'
        if r.status_code != 206 or r.headers.get('Content-Range') != expected:
            raise RuntimeError(f'Unexpected range response: {r.status_code}, {r.headers.get("Content-Range")}')
        data = r.content
        if len(data) != end - self.position:
            raise RuntimeError('Truncated archive range')
        self.position = end
        self.bytes_received += len(data)
        return data

    def close(self):
        self.session.close()
        super().close()


def metadata_rows(payload):
    # Official MAESTRO JSON has appeared in column-oriented and row-oriented forms.
    data = json.loads(payload)
    if isinstance(data, list):
        return data
    keys = range(len(data['midi_filename'])) if isinstance(data['midi_filename'], list) else list(data['midi_filename'])
    return [{column: values[k] for column, values in data.items()} for k in keys]


def obtain(config):
    manifest_path = ROOT / 'data/metadata/acquisition.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest['archive_url'] != config['archive_url']:
            raise RuntimeError('Archive changed; do not reuse data cache.')
        for path, digest in manifest['files'].items():
            if sha256(ROOT / path) != digest:
                raise RuntimeError(f'Data cache hash mismatch: {path}')
        rows = metadata_rows((ROOT / 'data/metadata/maestro-v3.0.0.json').read_bytes())
        candidates = sorted((r for r in rows if float(r['duration']) >= config['minimum_piece_duration_s']), key=lambda r: r['midi_filename'])
        if not candidates or candidates[0] != manifest['selected_piece']:
            raise RuntimeError('Selection no longer matches cached acquisition')
        return manifest
    with HTTPRangeReader(config['archive_url']) as remote:
        with zipfile.ZipFile(remote) as archive:
            metadata_name = 'maestro-v3.0.0/maestro-v3.0.0.json'
            metadata = archive.read(metadata_name)
            rows = metadata_rows(metadata)
            candidates = sorted((r for r in rows if float(r['duration']) >= config['minimum_piece_duration_s']), key=lambda r: r['midi_filename'])
            if not candidates:
                raise RuntimeError('No suitable metadata record')
            selected = candidates[0]
            filename = Path(selected['midi_filename'])
            if filename.is_absolute() or '..' in filename.parts:
                raise ValueError('Unsafe metadata filename')
            midi = archive.read('maestro-v3.0.0/' + filename.as_posix())
            paths = {'data/metadata/maestro-v3.0.0.json': metadata,
                     'data/maestro_midi/' + filename.as_posix(): midi}
            for rel, content in paths.items():
                out = ROOT / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(content)
            # Preserve license/readme when present; these are small provenance records.
            for name in archive.namelist():
                if Path(name).name.lower() in ('license', 'license.txt', 'readme', 'readme.txt'):
                    rel = 'data/metadata/' + Path(name).name
                    (ROOT / rel).write_bytes(archive.read(name))
                    paths[rel] = None
        manifest = {'dataset': 'MAESTRO', 'version': '3.0.0', 'archive_url': config['archive_url'],
                    'archive_etag': remote.etag, 'archive_bytes': remote.size,
                    'downloaded_bytes': remote.bytes_received, 'midi_members_downloaded': 1,
                    'metadata_records': len(rows), 'selected_piece': selected,
                    'files': {rel: sha256(ROOT / rel) for rel in paths}}
    write_json(manifest_path, manifest)
    write_json(ROOT / 'results/selection.json', manifest)
    return manifest


if __name__ == '__main__':
    print(json.dumps(obtain(load_config()), indent=2))
