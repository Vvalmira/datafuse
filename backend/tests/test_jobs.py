from app.jobs import aggregate_chunk_results, analyze_text_chunk, split_text


def test_split_text_chunks_by_words() -> None:
    assert split_text("one two three four five", 2) == ["one two", "three four", "five"]


def test_analyze_and_aggregate_text_chunks() -> None:
    chunks = ["Data data fuse", "fuse jobs jobs"]
    results = [analyze_text_chunk(chunk, index) for index, chunk in enumerate(chunks)]

    aggregate = aggregate_chunk_results(results)

    assert aggregate["word_count"] == 6
    assert aggregate["character_count"] == sum(len(chunk) for chunk in chunks)
    assert aggregate["top_terms"][0] == ("data", 2)
    assert ("jobs", 2) in aggregate["top_terms"]
    assert len(aggregate["chunks"]) == 2
