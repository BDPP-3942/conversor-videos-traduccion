from types import SimpleNamespace

from src.local_translation import LocalTranslationProvider


class FakeSentencePiece:
    def encode(self, text, out_type=str):
        return [text]

    def decode(self, tokens):
        return " ".join(tokens)


class FakeTranslator:
    def translate_batch(self, tokens, beam_size):
        assert beam_size == 2
        return [SimpleNamespace(hypotheses=[[item[0], "</s>"]]) for item in tokens]


def test_translate_batch_preserves_input_order_and_one_result_per_cue() -> None:
    provider = LocalTranslationProvider.__new__(LocalTranslationProvider)
    provider._source = FakeSentencePiece()
    provider._target = FakeSentencePiece()
    provider._translator = FakeTranslator()
    provider.settings = SimpleNamespace(local_translation_beam_size=2)

    assert provider.translate_batch(["uno", "dos", "tres"]) == ["uno", "dos", "tres"]


def test_translate_empty_batch_does_not_call_model() -> None:
    provider = LocalTranslationProvider.__new__(LocalTranslationProvider)
    provider._translator = None
    provider._source = None
    assert provider.translate_batch([]) == []
