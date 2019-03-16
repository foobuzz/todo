import unittest, sys
import os.path as op

from .utils import TestFunction

sys.path.insert(1, op.abspath('./todo'))

from todo import text_wrap


class TestSmartLine(TestFunction, unittest.TestCase):

	cases = [
		(['dummy'],           (True, '')),
		(['> citation'],      (True, '  ')),
		(['  >citation'],     (True, '   ')),
		(['## Heading'],      (True, '   ')),
		([' - Step 1'],       (True, '   ')),
		([' * Step 1'],       (True, '   ')),
		([' + Step 1'],       (True, '   ')),
		([' 1. Step 1'],      (True, '    ')),
		([' 2) Step 1'],      (True, '    ')),
		(['    def test():'], (False, ''))
	]

	def test_start_line(self):
		self.run_test(text_wrap.smart_line)


# https://jaspervdj.be/lorem-markdownum/

TEXT = """# Monte a intremuere

## Agam parum tua Salamis Iuppiter contigit Noemonaque

Lorem markdownum evocat. Ter sed corpore caeli [et
vacantem](http://partulumen.org/procul.html) corpora paratur liquidarum ast
multum, et!

> Unxit quia vitiumque vincis Iunonem non micantia quotiens seges **frequentes
> pariter Aesonis** adicit. Tota funera; namque sexta remeat tauri. Illi sorori,
> et erat: illo est admoveam, nec et Letoia tardus ducta habitata velantibus
> decusque, Cephalus? Opus inter rumpitque vocem voce arbore potestas Troasque
> facto, Pleiadasque sine adsiduae virgo, ingrediens, reverentia annua aversus!

## Quae ira vidi somnos

In **illo deductas** suis, sedesque saxa solet, dubitabile agris, tenet? Iulo
meritam Iovis educta grando Dixerat suis igni! Vici adhuc redimicula nuper
indulgens quoniam vicimus admovet et **Iovem**, languentique *meum*, insignia
perforat, imperat! Et fausto Tereus?

- Usa dum plangebat et tenet
- Sole secuta antra
- Frequentat lumina
- Gemina adplicat thalamos
- Rursus idem
- Porrigit fulmina me corpus nec talia neve"""


WRAPPED_30 = """# Monte a intremuere

## Agam parum tua Salamis
Iuppiter contigit Noemonaque

Lorem markdownum evocat. Ter
sed corpore caeli [et
vacantem](http://partulumen.or
g/procul.html) corpora paratur
liquidarum ast
multum, et!

> Unxit quia vitiumque vincis
Iunonem non micantia quotiens
seges **frequentes
> pariter Aesonis** adicit.
Tota funera; namque sexta
remeat tauri. Illi sorori,
> et erat: illo est admoveam,
nec et Letoia tardus ducta
habitata velantibus
> decusque, Cephalus? Opus
inter rumpitque vocem voce
arbore potestas Troasque
> facto, Pleiadasque sine
adsiduae virgo, ingrediens,
reverentia annua aversus!

## Quae ira vidi somnos

In **illo deductas** suis,
sedesque saxa solet,
dubitabile agris, tenet? Iulo
meritam Iovis educta grando
Dixerat suis igni! Vici adhuc
redimicula nuper
indulgens quoniam vicimus
admovet et **Iovem**,
languentique *meum*, insignia
perforat, imperat! Et fausto
Tereus?

- Usa dum plangebat et tenet
- Sole secuta antra
- Frequentat lumina
- Gemina adplicat thalamos
- Rursus idem
- Porrigit fulmina me corpus
nec talia neve"""


WRAPPED_30_SMART = """# Monte a intremuere

## Agam parum tua Salamis
   Iuppiter contigit
   Noemonaque

Lorem markdownum evocat. Ter
sed corpore caeli [et
vacantem](http://partulumen.or
g/procul.html) corpora paratur
liquidarum ast
multum, et!

> Unxit quia vitiumque vincis
  Iunonem non micantia
  quotiens seges **frequentes
> pariter Aesonis** adicit.
  Tota funera; namque sexta
  remeat tauri. Illi sorori,
> et erat: illo est admoveam,
  nec et Letoia tardus ducta
  habitata velantibus
> decusque, Cephalus? Opus
  inter rumpitque vocem voce
  arbore potestas Troasque
> facto, Pleiadasque sine
  adsiduae virgo, ingrediens,
  reverentia annua aversus!

## Quae ira vidi somnos

In **illo deductas** suis,
sedesque saxa solet,
dubitabile agris, tenet? Iulo
meritam Iovis educta grando
Dixerat suis igni! Vici adhuc
redimicula nuper
indulgens quoniam vicimus
admovet et **Iovem**,
languentique *meum*, insignia
perforat, imperat! Et fausto
Tereus?

- Usa dum plangebat et tenet
- Sole secuta antra
- Frequentat lumina
- Gemina adplicat thalamos
- Rursus idem
- Porrigit fulmina me corpus
  nec talia neve"""


class TestWrapText(TestFunction, unittest.TestCase):

	cases = [
		([TEXT, 30, False], WRAPPED_30),
		([TEXT, 30, True],  WRAPPED_30_SMART),
		([TEXT, 80, False], TEXT),  # [1] 
		([TEXT, 80, True],  TEXT)
	]

	# [1] Text is already wrapped at 80, so the test checks that the text
	# isn't altered

	def test_start_line(self):
		self.run_test(text_wrap.wrap_text)
