import pytest

from galaxy.datatypes.registry import example_datatype_registry_for_sample
from galaxy.datatypes.sniff import guess_ext
from galaxy.datatypes.text import Hocr
from galaxy.datatypes.xml import (
    AbbyyXml,
    Alto,
    PageXml,
)


XML_FORMATS = [
    (PageXml, "PcGts", "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"),
    (PageXml, "PcGts", "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"),
    (Alto, "alto", "http://www.loc.gov/standards/alto/ns-v4#"),
    (Alto, "alto", "http://www.loc.gov/standards/alto/ns-v2#"),
    (Alto, "alto", "http://schema.ccs-gmbh.com/ALTO"),
    (AbbyyXml, "document", "http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml"),
    (AbbyyXml, "document", "http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml"),
]


@pytest.fixture(scope="module")
def registry():
    return example_datatype_registry_for_sample()


@pytest.mark.parametrize("datatype,root,namespace", XML_FORMATS)
@pytest.mark.parametrize("prefixed", [False, True])
def test_ocr_xml(tmp_path, registry, datatype, root, namespace, prefixed):
    name = f"ocr:{root}" if prefixed else root
    declaration = "xmlns:ocr" if prefixed else "xmlns"
    path = tmp_path / "input"
    # No closing tag: sniffing must work from a document prefix.
    path.write_text(f'\ufeff<?xml version="1.0"?>\n<!-- OCR -->\n<{name}\n {declaration}="{namespace}">')
    assert datatype().sniff(str(path))
    assert guess_ext(str(path), registry.sniff_order) == datatype.file_ext


@pytest.mark.parametrize("datatype,root,namespace", XML_FORMATS)
@pytest.mark.parametrize("content", ["", "plain text", "<", "<!-- unclosed", '<document xmlns="urn:other"/>'])
def test_ocr_xml_rejects_other_content(tmp_path, datatype, root, namespace, content):
    path = tmp_path / "input"
    path.write_text(content)
    assert not datatype().sniff(str(path))


@pytest.mark.parametrize("datatype,root,namespace", XML_FORMATS)
def test_ocr_xml_requires_root_and_namespace(tmp_path, datatype, root, namespace):
    path = tmp_path / "input"
    for content in [
        f"<{root}/>",
        f'<other xmlns="{namespace}"/>',
        f'<wrapper><{root} xmlns="{namespace}"/></wrapper>',
    ]:
        path.write_text(content)
        assert not datatype().sniff(str(path))


@pytest.mark.parametrize("quote", ["'", '"'])
def test_hocr(tmp_path, registry, quote):
    path = tmp_path / "input"
    path.write_text(
        '<?xml version="1.0"?><!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml"><body>'
        f'<div class={quote}extra ocr_page another{quote}><span class="ocrx_word">Text</span>'
    )
    assert Hocr().sniff(str(path))
    assert guess_ext(str(path), registry.sniff_order) == "hocr"


@pytest.mark.parametrize(
    "content",
    [
        "",
        '<html><body>ocr_page</body></html>',
        '<html><div class="ocr_page_extra"></div></html>',
        '<html><!-- <div class="ocr_page"> --></html>',
        '<html><script>var text = \'<div class="ocr_page">\';</script></html>',
    ],
)
def test_hocr_rejects_other_content(tmp_path, content):
    path = tmp_path / "input"
    path.write_text(content)
    assert not Hocr().sniff(str(path))
