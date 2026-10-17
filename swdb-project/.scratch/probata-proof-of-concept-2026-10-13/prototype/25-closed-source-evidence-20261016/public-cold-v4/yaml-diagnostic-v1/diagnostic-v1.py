"""2026-10-16 ET. Read-only strict-YAML location diagnostic; no scientific audit."""
import base64, hashlib, json, os, re, resource, signal, stat, sys, time
from pathlib import Path
YAML_BYTES=base64.b64decode('IiIiMjAyNi0xMC0xNiBFVC4gU3RyaWN0IG5vLXRhZy9uby1hbmNob3IgcmVhZGVyIGZvciB5YW1saW8ncyBKU09OLXNoYXBlZCBvdXRwdXQuCgpJbmRlcGVuZGVudCBvYnNlcnZlciBvbmx5LiBVbmtub3duIFlBTUwgc3ludGF4IHJlZnVzZXM7IG5ldmVyIGV4ZWN1dGUgYSBsb2FkZXIuClRoZSBlbWl0dGluZyB5YW1saW8gc291cmNlIGRpc2FibGVzIGFsaWFzZXMgYW5kIHVzZXMgbGl0ZXJhbCBtdWx0aWxpbmUgc3RyaW5ncy4KIiIiCmltcG9ydCBqc29uCmltcG9ydCBtYXRoCmltcG9ydCByZQoKCmRlZiBuZWVkKG9rLCBtZXNzYWdlKToKICAgIGlmIG5vdCBvazoKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKG1lc3NhZ2UpCgoKZGVmIHNjYWxhcih0ZXh0KToKICAgIHRleHQgPSB0ZXh0LnN0cmlwKCkKICAgIG5lZWQodGV4dCBhbmQgbm90IHRleHQuc3RhcnRzd2l0aCgoJyEnLCAnJicsICcqJywgJz4nLCAnfCcsICc/JywgJyUnLCAnIycsICdAJywgJ2AnLCAnLCcsICddJywgJ30nKSksICd1bnN1cHBvcnRlZCBZQU1MIHNjYWxhciBzeW50YXgnKQogICAgaWYgdGV4dC5zdGFydHN3aXRoKCciJyk6CiAgICAgICAgdmFsdWUgPSBqc29uLmxvYWRzKHRleHQpCiAgICAgICAgbmVlZChpc2luc3RhbmNlKHZhbHVlLCBzdHIpLCAncXVvdGVkIFlBTUwgc2NhbGFyIGlzIG5vdCB0ZXh0JykKICAgICAgICByZXR1cm4gdmFsdWUKICAgIGlmIHRleHQuc3RhcnRzd2l0aCgiJyIpOgogICAgICAgIG5lZWQobGVuKHRleHQpID49IDIgYW5kIHRleHQuZW5kc3dpdGgoIiciKSwgJ3VuY2xvc2VkIHNpbmdsZSBxdW90ZWQgc2NhbGFyJykKICAgICAgICBib2R5ID0gdGV4dFsxOi0xXQogICAgICAgIG5lZWQoIiciIG5vdCBpbiBib2R5LnJlcGxhY2UoIicnIiwgJycpLCAndW5wYWlyZWQgWUFNTCBxdW90ZScpCiAgICAgICAgcmV0dXJuIGJvZHkucmVwbGFjZSgiJyciLCAiJyIpCiAgICBpZiB0ZXh0IGluICgnbnVsbCcsICd+Jyk6CiAgICAgICAgcmV0dXJuIE5vbmUKICAgIGlmIHRleHQgaW4gKCd0cnVlJywgJ2ZhbHNlJyk6CiAgICAgICAgcmV0dXJuIHRleHQgPT0gJ3RydWUnCiAgICBuZWVkKHRleHQubG93ZXIoKSBub3QgaW4gKCd5ZXMnLCAnbm8nLCAnb24nLCAnb2ZmJywgJy5uYW4nLCAnLmluZicsICcrLmluZicsICctLmluZicsICd0cnVlJywgJ2ZhbHNlJywgJ251bGwnKQogICAgICAgICBhbmQgbm90IHJlLmZ1bGxtYXRjaChyJ1stK10/MCg/Oltib3hdWzAtOWEtZkEtRl9dK3xbMC05X10rKScsIHRleHQpCiAgICAgICAgIGFuZCBub3QgcmUuZnVsbG1hdGNoKHInWy0rXT9bMC05XSsoPzo6WzAtOV0rKSsoPzpcLlswLTldKik/JywgdGV4dCksCiAgICAgICAgICdub25jYW5vbmljYWwgWUFNTCBpbXBsaWNpdCBzY2FsYXInKQogICAgaWYgcmUuZnVsbG1hdGNoKHInLT8oPzowfFsxLTldWzAtOV0qKScsIHRleHQpOgogICAgICAgIHJldHVybiBpbnQodGV4dCkKICAgIGlmIHJlLmZ1bGxtYXRjaChyJy0/KD86WzAtOV0rXC5bMC05XSp8XC5bMC05XSspKD86W2VFXVstK10/WzAtOV0rKT8nLCB0ZXh0KToKICAgICAgICB2YWx1ZSA9IGZsb2F0KHRleHQpCiAgICAgICAgbmVlZChtYXRoLmlzZmluaXRlKHZhbHVlKSwgJ25vbmZpbml0ZSBZQU1MIG51bWJlcicpCiAgICAgICAgcmV0dXJuIHZhbHVlCiAgICBuZWVkKG5vdCByZS5mdWxsbWF0Y2gocidbLStdPyg/OlswLTldWzAtOV9dKig/OlwuWzAtOV9dKik/KD86W2VFXVstK10/WzAtOV0rKT98XC5bMC05X10rKD86W2VFXVstK10/WzAtOV0rKT8pJyx0ZXh0KSwKICAgICAgICAgJ25vbmNhbm9uaWNhbCBZQU1MIG51bWVyaWMgc2NhbGFyJykKICAgIG5lZWQobm90IHRleHQuc3RhcnRzd2l0aCgoJ1snLCAneycpKSBhbmQgJyAjJyBub3QgaW4gdGV4dCBhbmQgJzogJyBub3QgaW4gdGV4dCwgJ3Vuc3VwcG9ydGVkIHBsYWluIFlBTUwgc2NhbGFyJykKICAgIHJldHVybiB0ZXh0CgoKZGVmIGZsb3codGV4dCk6CiAgICBpbmRleCA9IDAKICAgIGRlZiBzcGFjZSgpOgogICAgICAgIG5vbmxvY2FsIGluZGV4CiAgICAgICAgd2hpbGUgaW5kZXggPCBsZW4odGV4dCkgYW5kIHRleHRbaW5kZXhdLmlzc3BhY2UoKToKICAgICAgICAgICAgaW5kZXggKz0gMQogICAgZGVmIGF0b20oa2V5PUZhbHNlKToKICAgICAgICBub25sb2NhbCBpbmRleAogICAgICAgIHNwYWNlKCk7IHN0YXJ0ID0gaW5kZXgKICAgICAgICBuZWVkKGluZGV4IDwgbGVuKHRleHQpLCAnbWlzc2luZyBmbG93IHZhbHVlJykKICAgICAgICBpZiB0ZXh0W2luZGV4XSBpbiAiXCInIjoKICAgICAgICAgICAgcXVvdGUgPSB0ZXh0W2luZGV4XTsgaW5kZXggKz0gMQogICAgICAgICAgICB3aGlsZSBpbmRleCA8IGxlbih0ZXh0KToKICAgICAgICAgICAgICAgIGlmIHRleHRbaW5kZXhdID09IHF1b3RlOgogICAgICAgICAgICAgICAgICAgIGlmIHF1b3RlID09ICInIiBhbmQgdGV4dFtpbmRleDppbmRleCsyXSA9PSAiJyciOgogICAgICAgICAgICAgICAgICAgICAgICBpbmRleCArPSAyOyBjb250aW51ZQogICAgICAgICAgICAgICAgICAgIGluZGV4ICs9IDE7IGJyZWFrCiAgICAgICAgICAgICAgICBpZiBxdW90ZSA9PSAnIicgYW5kIHRleHRbaW5kZXhdID09ICdcXCc6CiAgICAgICAgICAgICAgICAgICAgaW5kZXggKz0gMgogICAgICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgICAgICBpbmRleCArPSAxCiAgICAgICAgICAgIHJldHVybiBzY2FsYXIodGV4dFtzdGFydDppbmRleF0pCiAgICAgICAgaWYgdGV4dFtpbmRleF0gaW4gJ1t7JzoKICAgICAgICAgICAgb3BlbmVyID0gdGV4dFtpbmRleF07IGNsb3NlciA9ICddJyBpZiBvcGVuZXIgPT0gJ1snIGVsc2UgJ30nOyBpbmRleCArPSAxCiAgICAgICAgICAgIHJlc3VsdCA9IFtdIGlmIG9wZW5lciA9PSAnWycgZWxzZSB7fQogICAgICAgICAgICBzcGFjZSgpCiAgICAgICAgICAgIGlmIGluZGV4IDwgbGVuKHRleHQpIGFuZCB0ZXh0W2luZGV4XSA9PSBjbG9zZXI6CiAgICAgICAgICAgICAgICBpbmRleCArPSAxOyByZXR1cm4gcmVzdWx0CiAgICAgICAgICAgIHdoaWxlIFRydWU6CiAgICAgICAgICAgICAgICB2YWx1ZSA9IGF0b20ob3BlbmVyID09ICd7JykKICAgICAgICAgICAgICAgIGlmIG9wZW5lciA9PSAnWyc6CiAgICAgICAgICAgICAgICAgICAgcmVzdWx0LmFwcGVuZCh2YWx1ZSkKICAgICAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICAgICAgbmVlZChpc2luc3RhbmNlKHZhbHVlLCBzdHIpIGFuZCB2YWx1ZSBub3QgaW4gcmVzdWx0LCAnZmxvdyBrZXkgZHVwbGljYXRlL3R5cGUnKQogICAgICAgICAgICAgICAgICAgIHNwYWNlKCk7IG5lZWQoaW5kZXggPCBsZW4odGV4dCkgYW5kIHRleHRbaW5kZXhdID09ICc6JywgJ2Zsb3cgbWFwcGluZyBzZXBhcmF0b3InKTsgaW5kZXggKz0gMQogICAgICAgICAgICAgICAgICAgIHJlc3VsdFt2YWx1ZV0gPSBhdG9tKCkKICAgICAgICAgICAgICAgIHNwYWNlKCk7IG5lZWQoaW5kZXggPCBsZW4odGV4dCksICd1bmNsb3NlZCBZQU1MIGZsb3cgdmFsdWUnKQogICAgICAgICAgICAgICAgaWYgdGV4dFtpbmRleF0gPT0gY2xvc2VyOgogICAgICAgICAgICAgICAgICAgIGluZGV4ICs9IDE7IHJldHVybiByZXN1bHQKICAgICAgICAgICAgICAgIG5lZWQodGV4dFtpbmRleF0gPT0gJywnLCAnZmxvdyBpdGVtIHNlcGFyYXRvcicpOyBpbmRleCArPSAxCiAgICAgICAgd2hpbGUgaW5kZXggPCBsZW4odGV4dCkgYW5kIHRleHRbaW5kZXhdIG5vdCBpbiAoJyxdfTonIGlmIGtleSBlbHNlICcsXX0nKToKICAgICAgICAgICAgaW5kZXggKz0gMQogICAgICAgIHJldHVybiBzY2FsYXIodGV4dFtzdGFydDppbmRleF0pCiAgICB2YWx1ZSA9IGF0b20oKTsgc3BhY2UoKTsgbmVlZChpbmRleCA9PSBsZW4odGV4dCksICd0cmFpbGluZyBmbG93IFlBTUwgYnl0ZXMnKQogICAgcmV0dXJuIHZhbHVlCgoKY2xhc3MgUmVhZGVyOgogICAgZGVmIF9faW5pdF9fKHNlbGYsIHJhdyk6CiAgICAgICAgc2VsZi5saW5lcyA9IHJhdy5kZWNvZGUoJ3V0Zi04Jykuc3BsaXRsaW5lcygpCiAgICAgICAgbmVlZChub3QgYW55KCdcdCcgaW4gbGluZVs6bGVuKGxpbmUpLWxlbihsaW5lLmxzdHJpcCgpKV0gZm9yIGxpbmUgaW4gc2VsZi5saW5lcyksICdZQU1MIGluZGVudGF0aW9uIHRhYicpCiAgICAgICAgc2VsZi5hdCA9IDAKICAgICAgICBzZWxmLm5vZGVzID0gMAogICAgZGVmIHNraXAoc2VsZik6CiAgICAgICAgd2hpbGUgc2VsZi5hdCA8IGxlbihzZWxmLmxpbmVzKSBhbmQgbm90IHNlbGYubGluZXNbc2VsZi5hdF0uc3RyaXAoKToKICAgICAgICAgICAgc2VsZi5hdCArPSAxCiAgICBkZWYgaW5kZW50YXRpb24oc2VsZik6CiAgICAgICAgcmV0dXJuIGxlbihzZWxmLmxpbmVzW3NlbGYuYXRdKSAtIGxlbihzZWxmLmxpbmVzW3NlbGYuYXRdLmxzdHJpcCgnICcpKQogICAgZGVmIHNwbGl0KHNlbGYsIHRleHQpOgogICAgICAgIHF1b3RlID0gTm9uZTsgZGVwdGggPSAwOyBhdCA9IDAKICAgICAgICB3aGlsZSBhdCA8IGxlbih0ZXh0KToKICAgICAgICAgICAgY2ggPSB0ZXh0W2F0XQogICAgICAgICAgICBpZiBxdW90ZToKICAgICAgICAgICAgICAgIGlmIGNoID09IHF1b3RlOgogICAgICAgICAgICAgICAgICAgIGlmIHF1b3RlID09ICInIiBhbmQgdGV4dFthdDphdCsyXSA9PSAiJyciOgogICAgICAgICAgICAgICAgICAgICAgICBhdCArPSAyOyBjb250aW51ZQogICAgICAgICAgICAgICAgICAgIHF1b3RlID0gTm9uZQogICAgICAgICAgICAgICAgZWxpZiBxdW90ZSA9PSAnIicgYW5kIGNoID09ICdcXCc6CiAgICAgICAgICAgICAgICAgICAgYXQgKz0gMjsgY29udGludWUKICAgICAgICAgICAgZWxpZiBjaCBpbiAiXCInIjoKICAgICAgICAgICAgICAgIHF1b3RlID0gY2gKICAgICAgICAgICAgZWxpZiBjaCBpbiAnW3snOiBkZXB0aCArPSAxCiAgICAgICAgICAgIGVsaWYgY2ggaW4gJ119JzogZGVwdGggLT0gMQogICAgICAgICAgICBlbGlmIGNoID09ICc6JyBhbmQgbm90IGRlcHRoIGFuZCAoYXQrMSA9PSBsZW4odGV4dCkgb3IgdGV4dFthdCsxXS5pc3NwYWNlKCkpOgogICAgICAgICAgICAgICAgcmV0dXJuIHRleHRbOmF0XSwgdGV4dFthdCsxOl0ubHN0cmlwKCkKICAgICAgICAgICAgYXQgKz0gMQogICAgICAgIHJldHVybiBOb25lCiAgICBkZWYgdmFsdWUoc2VsZiwgdmFsdWUsIGluZGVudCk6CiAgICAgICAgaWYgcmUuZnVsbG1hdGNoKHInXHxbMS05XT9bKy1dPycsIHZhbHVlKToKICAgICAgICAgICAgIyB5YW1saW8gZW1pdHMgYSBsaXRlcmFsIGJsb2NrIGZvciBldmVyeSBhY3R1YWwgbmV3bGluZS1iZWFyaW5nIHN0ci4KICAgICAgICAgICAgbWF0Y2ggPSByZS5mdWxsbWF0Y2gocidcfChbMS05XT8pKFsrLV0/KScsIHZhbHVlKTsgaW5kaWNhdG9yLCBjaG9tcCA9IG1hdGNoLmdyb3VwcygpCiAgICAgICAgICAgIGZpcnN0ID0gc2VsZi5hdAogICAgICAgICAgICBwcm9iZSA9IGZpcnN0CiAgICAgICAgICAgIHdoaWxlIHByb2JlIDwgbGVuKHNlbGYubGluZXMpIGFuZCBub3Qgc2VsZi5saW5lc1twcm9iZV0uc3RyaXAoKTogcHJvYmUgKz0gMQogICAgICAgICAgICBiYXNlID0gaW5kZW50ICsgaW50KGluZGljYXRvcikgaWYgaW5kaWNhdG9yIGVsc2UgKGxlbihzZWxmLmxpbmVzW3Byb2JlXSktbGVuKHNlbGYubGluZXNbcHJvYmVdLmxzdHJpcCgnICcpKSBpZiBwcm9iZSA8IGxlbihzZWxmLmxpbmVzKSBlbHNlIGluZGVudCsyKQogICAgICAgICAgICBuZWVkKGJhc2UgPiBpbmRlbnQsICdsaXRlcmFsIGJsb2NrIGluZGVudGF0aW9uJykKICAgICAgICAgICAgcGFydHMgPSBbXQogICAgICAgICAgICB3aGlsZSBzZWxmLmF0IDwgbGVuKHNlbGYubGluZXMpOgogICAgICAgICAgICAgICAgbGluZSA9IHNlbGYubGluZXNbc2VsZi5hdF0KICAgICAgICAgICAgICAgIGlmIGxpbmUuc3RyaXAoKSBhbmQgbGVuKGxpbmUpLWxlbihsaW5lLmxzdHJpcCgnICcpKSA8IGJhc2U6IGJyZWFrCiAgICAgICAgICAgICAgICBwYXJ0cy5hcHBlbmQobGluZVtiYXNlOl0gaWYgbGluZS5zdHJpcCgpIGVsc2UgJycpCiAgICAgICAgICAgICAgICBzZWxmLmF0ICs9IDEKICAgICAgICAgICAgdGV4dCA9ICdcbicuam9pbihwYXJ0cykrJ1xuJwogICAgICAgICAgICBpZiBjaG9tcCA9PSAnLSc6IHJldHVybiB0ZXh0LnJzdHJpcCgnXG4nKQogICAgICAgICAgICBpZiBjaG9tcCA9PSAnKyc6IHJldHVybiB0ZXh0CiAgICAgICAgICAgIHJldHVybiB0ZXh0LnJzdHJpcCgnXG4nKSsnXG4nCiAgICAgICAgaWYgbm90IHZhbHVlOgogICAgICAgICAgICBzZWxmLnNraXAoKQogICAgICAgICAgICBpZiBzZWxmLmF0ID09IGxlbihzZWxmLmxpbmVzKSBvciBzZWxmLmluZGVudGF0aW9uKCkgPCBpbmRlbnQ6CiAgICAgICAgICAgICAgICByZXR1cm4gTm9uZQogICAgICAgICAgICBpZiBzZWxmLmluZGVudGF0aW9uKCkgPT0gaW5kZW50IGFuZCBub3Qgc2VsZi5saW5lc1tzZWxmLmF0XS5sc3RyaXAoKS5zdGFydHN3aXRoKCctICcpOgogICAgICAgICAgICAgICAgcmV0dXJuIE5vbmUKICAgICAgICAgICAgcmV0dXJuIHNlbGYuYmxvY2soc2VsZi5pbmRlbnRhdGlvbigpKQogICAgICAgICMgTG9uZyBwbGFpbi9xdW90ZWQvZmxvdyBzdHJpbmdzIGFyZSBmb2xkZWQgYnkgdGhlIGZpeGVkIHdpZHRoIGVtaXR0ZXIuCiAgICAgICAgd2hpbGUgc2VsZi5hdCA8IGxlbihzZWxmLmxpbmVzKToKICAgICAgICAgICAgbGluZSA9IHNlbGYubGluZXNbc2VsZi5hdF0KICAgICAgICAgICAgaWYgbm90IGxpbmUuc3RyaXAoKTogYnJlYWsKICAgICAgICAgICAgYW1vdW50ID0gbGVuKGxpbmUpLWxlbihsaW5lLmxzdHJpcCgnICcpKQogICAgICAgICAgICBpZiBhbW91bnQgPD0gaW5kZW50OiBicmVhawogICAgICAgICAgICB2YWx1ZSArPSAnICcrbGluZS5zdHJpcCgpOyBzZWxmLmF0ICs9IDEKICAgICAgICByZXR1cm4gZmxvdyh2YWx1ZSkgaWYgdmFsdWUuc3RhcnRzd2l0aCgoJ1snLCAneycpKSBlbHNlIHNjYWxhcih2YWx1ZSkKICAgIGRlZiBibG9jayhzZWxmLCBpbmRlbnQpOgogICAgICAgIHNlbGYubm9kZXMgKz0gMTsgbmVlZChzZWxmLm5vZGVzIDwgMjAwMDAwLCAnWUFNTCBub2RlIGJ1ZGdldCcpCiAgICAgICAgc2VsZi5za2lwKCk7IG5lZWQoc2VsZi5hdCA8IGxlbihzZWxmLmxpbmVzKSBhbmQgc2VsZi5pbmRlbnRhdGlvbigpID09IGluZGVudCwgJ1lBTUwgYmxvY2sgaW5kZW50YXRpb24nKQogICAgICAgIHNlcXVlbmNlID0gc2VsZi5saW5lc1tzZWxmLmF0XVtpbmRlbnQ6XS5zdGFydHN3aXRoKCctICcpCiAgICAgICAgcmVzdWx0ID0gW10gaWYgc2VxdWVuY2UgZWxzZSB7fQogICAgICAgIHdoaWxlIHNlbGYuYXQgPCBsZW4oc2VsZi5saW5lcyk6CiAgICAgICAgICAgIHNlbGYuc2tpcCgpCiAgICAgICAgICAgIGlmIHNlbGYuYXQgPT0gbGVuKHNlbGYubGluZXMpIG9yIHNlbGYuaW5kZW50YXRpb24oKSA8IGluZGVudDogYnJlYWsKICAgICAgICAgICAgaWYgc2VsZi5pbmRlbnRhdGlvbigpICE9IGluZGVudDogYnJlYWsKICAgICAgICAgICAgdGV4dCA9IHNlbGYubGluZXNbc2VsZi5hdF1baW5kZW50Ol0KICAgICAgICAgICAgaWYgdGV4dC5zdGFydHN3aXRoKCctICcpICE9IHNlcXVlbmNlOiBicmVhawogICAgICAgICAgICBzZWxmLmF0ICs9IDEKICAgICAgICAgICAgaWYgc2VxdWVuY2U6CiAgICAgICAgICAgICAgICB0YWlsID0gdGV4dFsyOl07IHBhaXIgPSBzZWxmLnNwbGl0KHRhaWwpCiAgICAgICAgICAgICAgICBpZiBwYWlyOgogICAgICAgICAgICAgICAgICAgIGtleSwgdmFsdWUgPSBwYWlyOyBrZXkgPSBzY2FsYXIoa2V5KTsgbmVlZChpc2luc3RhbmNlKGtleSxzdHIpLCAnWUFNTCBtYXBwaW5nIGtleScpCiAgICAgICAgICAgICAgICAgICAgaXRlbSA9IHtrZXk6c2VsZi52YWx1ZSh2YWx1ZSxpbmRlbnQrMil9CiAgICAgICAgICAgICAgICAgICAgc2VsZi5za2lwKCkKICAgICAgICAgICAgICAgICAgICBpZiBzZWxmLmF0IDwgbGVuKHNlbGYubGluZXMpIGFuZCBzZWxmLmluZGVudGF0aW9uKCkgPT0gaW5kZW50KzI6CiAgICAgICAgICAgICAgICAgICAgICAgIHJlc3QgPSBzZWxmLmJsb2NrKGluZGVudCsyKQogICAgICAgICAgICAgICAgICAgICAgICBuZWVkKGlzaW5zdGFuY2UocmVzdCxkaWN0KSBhbmQgbm90IHNldChpdGVtKS5pbnRlcnNlY3Rpb24ocmVzdCksICdZQU1MIGxpc3QgbWFwcGluZyBkdXBsaWNhdGUnKQogICAgICAgICAgICAgICAgICAgICAgICBpdGVtLnVwZGF0ZShyZXN0KQogICAgICAgICAgICAgICAgICAgIHJlc3VsdC5hcHBlbmQoaXRlbSkKICAgICAgICAgICAgICAgIGVsc2U6IHJlc3VsdC5hcHBlbmQoc2VsZi52YWx1ZSh0YWlsLGluZGVudCkpCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICBwYWlyID0gc2VsZi5zcGxpdCh0ZXh0KTsgbmVlZChwYWlyIGlzIG5vdCBOb25lLCAnWUFNTCBtYXBwaW5nIGNvbG9uJykKICAgICAgICAgICAgICAgIGtleSwgdmFsdWUgPSBwYWlyOyBrZXkgPSBzY2FsYXIoa2V5KQogICAgICAgICAgICAgICAgbmVlZChpc2luc3RhbmNlKGtleSxzdHIpIGFuZCBrZXkgbm90IGluIHJlc3VsdCwgJ1lBTUwgbWFwcGluZyBkdXBsaWNhdGUva2V5IHR5cGUnKQogICAgICAgICAgICAgICAgcmVzdWx0W2tleV0gPSBzZWxmLnZhbHVlKHZhbHVlLGluZGVudCkKICAgICAgICByZXR1cm4gcmVzdWx0CgoKZGVmIGxvYWRzKHJhdyk6CiAgICByZWFkZXIgPSBSZWFkZXIocmF3KTsgcmVhZGVyLnNraXAoKQogICAgbmVlZChyZWFkZXIuYXQgPCBsZW4ocmVhZGVyLmxpbmVzKSwgJ2VtcHR5IFlBTUwgZG9jdW1lbnQnKQogICAgcmVzdWx0ID0gcmVhZGVyLmJsb2NrKHJlYWRlci5pbmRlbnRhdGlvbigpKTsgcmVhZGVyLnNraXAoKQogICAgbmVlZChyZWFkZXIuYXQgPT0gbGVuKHJlYWRlci5saW5lcyksICd1bmNvbnN1bWVkIG9yIHVuc3VwcG9ydGVkIFlBTUwgc3ludGF4JykKICAgIHJldHVybiByZXN1bHQK')
YAML_SHA='467cef5049fc30f730f0176f7db336952f6ce006ec11a9b2872abec9ca53daf9'
ROOT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-1433b8f5-t25-closed-source-public-v4')
PREFIX='test_public_closed_source_proo'
CASES=('safe','missing_bundle','stale_method','wrong_result','default_method')
LIMIT=8*1024*1024
KNOWN_ERRORS=frozenset(('YAML mapping colon','YAML indentation tab','YAML block indentation','YAML node budget','YAML mapping key','YAML list mapping duplicate','YAML mapping duplicate/key type','empty YAML document','unconsumed or unsupported YAML syntax','unsupported YAML scalar syntax','quoted YAML scalar is not text','unclosed single quoted scalar','unpaired YAML quote','noncanonical YAML implicit scalar','nonfinite YAML number','noncanonical YAML numeric scalar','unsupported plain YAML scalar','missing flow value','flow key duplicate/type','flow mapping separator','unclosed YAML flow value','flow item separator','trailing flow YAML bytes','literal block indentation'))

def need(ok,message):
    if not ok: raise ValueError(message)

def stable(s):
    return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def read(path):
    need(path.is_absolute() and ROOT in path.parents,'outside exact diagnostic root')
    for parent in (ROOT,*reversed(path.relative_to(ROOT).parents[:-1])):
        candidate=parent if parent==ROOT else ROOT/parent
        need(stat.S_ISDIR(candidate.lstat().st_mode),'nonphysical diagnostic parent')
    before=path.lstat();need(stat.S_ISREG(before.st_mode) and before.st_size<=LIMIT,'bounded regular diagnostic input')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        need(stable(os.fstat(fd))==stable(before),'opened identity differs')
        chunks=[];total=0
        while True:
            block=os.read(fd,min(65536,LIMIT+1-total))
            if not block: break
            total+=len(block);need(total<=LIMIT,'diagnostic input grew');chunks.append(block)
        need(stable(os.fstat(fd))==stable(before),'diagnostic input changed while read')
    finally:os.close(fd)
    need(stable(path.lstat())==stable(before),'diagnostic input replaced')
    data=b''.join(chunks);need(len(data)==before.st_size,'diagnostic input size changed')
    return data,{'relative':str(path.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'stable':stable(before)}

def shape(lines,index):
    line=lines[index];text=line.lstrip(' ')
    return {'line':index+1,'characters':len(line),'indent':len(line)-len(text),'blank':not text.strip(),
        'comment':text.startswith('#'),'sequence_marker':text.startswith('- '),'document_marker':text in ('---','...'),
        'single_quote_leading':text.startswith("'"),'double_quote_leading':text.startswith(chr(34)),
        'flow_leading':text.startswith(('[','{')),'contains_colon':':' in text,'ends_colon':text.endswith(':')}

def locate(data,reader_class):
    reader=reader_class(data)
    try:
        reader.skip();need(reader.at<len(reader.lines),'empty YAML document')
        value=reader.block(reader.indentation());reader.skip()
        need(reader.at==len(reader.lines),'unconsumed or unsupported YAML syntax')
        return {'parsed':True,'nodes':reader.nodes,'line_count':len(reader.lines),'semantic_values_returned':False}
    except (ValueError,TypeError,IndexError,UnicodeError) as exc:
        tb=exc.__traceback__;frames=[];candidate=max(0,min(len(reader.lines)-1,reader.at-1));context_indent=None
        while tb:
            frame=tb.tb_frame;name=frame.f_code.co_name;frames.append(name)
            if frame.f_locals.get('self') is reader and name=='block':
                candidate=max(0,min(len(reader.lines)-1,reader.at-1));context_indent=frame.f_locals.get('indent')
            tb=tb.tb_next
        message=str(exc)
        return {'parsed':False,'exception':type(exc).__name__,'category':message if message in KNOWN_ERRORS else 'unclassified parser error',
            'reader_at_zero_based':reader.at,'candidate_line':candidate+1,'block_indent':context_indent,
            'frames':frames,'line_count':len(reader.lines),'nodes':reader.nodes,
            'nearby_shape':[shape(reader.lines,i) for i in range(max(0,candidate-3),min(len(reader.lines),candidate+4))],
            'semantic_values_returned':False}

def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
        raise RuntimeError('diagnostic forbids tools/children/network/native libraries')
    if event=='open':
        mode=args[1];flags=args[2]
        need(not (isinstance(mode,str) and any(c in mode for c in 'wax+')) and not flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND),'diagnostic forbids writable open')
    if event in ('os.remove','os.rmdir','os.mkdir','os.rename','os.link','os.symlink','os.chmod','os.chown','os.truncate','os.utime'):
        raise RuntimeError('diagnostic forbids mutation')
    if event=='import' and args[0].split('.')[0] in ('swdb','yaml','pytest','clang','ctypes','psutil'):
        raise RuntimeError('diagnostic forbids project/third-party/native import')

def main():
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('diagnostic alarm')));signal.alarm(45)
    sys.addaudithook(audit);need(hashlib.sha256(YAML_BYTES).hexdigest()==YAML_SHA,'frozen reader mismatch')
    ns={'__name__':'frozen_independent_yaml'};exec(compile(YAML_BYTES,'record_yaml_subset.py','exec'),ns)
    rows=[];observed=[];started=time.monotonic()
    for i,case in enumerate(CASES):
        base=ROOT/'closed-source-profile/pytest'/(PREFIX+str(i))
        record_raw,record_pin=read(base/'retained-public-record.json');observed.append((base/'retained-public-record.json',record_pin))
        record=json.loads(record_raw);identifier=record['id']
        need(isinstance(identifier,str) and re.fullmatch(r'proof\.[A-Za-z0-9_.-]+',identifier),'proof identifier not a safe exact filename')
        method='wp-vector-closed-default-v1' if case=='default_method' else 'wp-vector-closed-source-v1'
        for phase,path in (('proof',base/'records/proofs'/(identifier+'.yaml')),
                           ('method',base/'library/methods'/(method+'.yaml')),
                           ('contract',base/'library/rewrite_contracts/fixture_vector_closed_no_growth.yaml')):
            data,pin=read(path);observed.append((path,pin));out=locate(data,ns['Reader'])
            rows.append({'case':case,'phase':phase,'input':pin,'syntax':out})
    for path,pin in observed:
        _,again=read(path);need(again==pin,'diagnostic final input identity changed')
    result={'date':'2026-10-16 ET','diagnostic':'strict-YAML structural location only','raw_root':str(ROOT),
        'reader_sha256':YAML_SHA,'inputs':len(observed),'yaml_files':len(rows),'rows':rows,
        'seconds':time.monotonic()-started,'raw_source_or_yaml_values_transferred':False,
        'compiler_or_verifier_or_project_executed':False,'scientific_or_source_or_caller_admission':False}
    output=json.dumps(result,sort_keys=True);need(len(output.encode())<32768,'diagnostic output budget');print(output)

if __name__=='__main__':main()
