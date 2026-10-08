from generation.llm.sse import decode_chunk


def test_decodes_text_delta():
    chunk = decode_chunk({"choices": [{"delta": {"content": "Hello"}}]})
    assert chunk is not None
    assert chunk.text == "Hello"


def test_decodes_finish_reason():
    payload = {"choices": [{"delta": {}, "finish_reason": "stop"}]}
    chunk = decode_chunk(payload)
    assert chunk is not None
    assert chunk.finish_reason == "stop"


def test_decodes_usage_only_chunk():
    payload = {
        "choices": [],
        "usage": {"prompt_tokens": 10, "completion_tokens": 2},
    }
    chunk = decode_chunk(payload)
    assert chunk is not None
    assert chunk.tokens_in == 10
    assert chunk.tokens_out == 2


def test_empty_payload_returns_none():
    assert decode_chunk({}) is None
    assert decode_chunk({"choices": [{"delta": {}}]}) is None


def test_tolerates_missing_keys():
    assert decode_chunk({"id": "chunk-1", "choices": []}) is None
