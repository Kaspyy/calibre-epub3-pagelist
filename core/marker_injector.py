"""
Marker injector for EPUB3 page break elements.

Inserts ``<span role="doc-pagebreak" epub:type="pagebreak">`` elements
into EPUB XHTML content documents at positions determined by the Paginator.
"""
from collections import defaultdict
from lxml import etree

XHTML_NS = "http://www.w3.org/1999/xhtml"
EPUB_OPS_NS = "http://www.idpf.org/2007/ops"


class MarkerInjector:
    """Injects page break marker ``<span>`` elements into EPUB content documents."""

    def __init__(self, container):
        """
        :param container: Calibre Polish Container.
        """
        self.container = container

    def inject_markers(self, page_breaks: list) -> int:
        """
        Inject page break markers for all PageBreak objects.

        Markers are inserted in reverse document order within each spine
        document so that earlier element indices remain valid.

        :param page_breaks: List of PageBreak objects from the Paginator.
        :return: Count of successfully injected markers.
        """
        count = 0

        # Group page breaks by spine document
        grouped: dict[str, list] = defaultdict(list)
        for pb in page_breaks:
            grouped[pb.spine_name].append(pb)

        for spine_name, pbs in grouped.items():
            # Parse the document (cached by the container)
            self.container.parsed(spine_name)

            # Process in reverse order to preserve element positions
            for pb in reversed(pbs):
                ref_element = pb.insert_element
                parent = ref_element.getparent()

                if parent is None:
                    continue

                span = self._create_pagebreak_element(pb)
                insert_pos = getattr(pb, 'insert_position', 'after')
                if insert_pos == 'before':
                    self._insert_before_element(parent, ref_element, span)
                else:
                    self._insert_after_element(parent, ref_element, span)
                count += 1

            self.container.dirty(spine_name)

        return count

    def _create_pagebreak_element(self, page_break) -> etree._Element:
        """
        Create a properly namespaced XHTML ``<span>`` element for a page break.

        Produces::

            <span id="page_42"
                  role="doc-pagebreak"
                  epub:type="pagebreak"
                  aria-label="42"/>
        """
        span = etree.Element(
            f"{{{XHTML_NS}}}span",
            nsmap={'epub': EPUB_OPS_NS},
        )
        span.set("id", page_break.anchor_id)
        span.set("role", "doc-pagebreak")
        span.set(f"{{{EPUB_OPS_NS}}}type", "pagebreak")
        span.set("aria-label", page_break.page_label)
        return span

    def _insert_after_element(
        self,
        parent: etree._Element,
        ref_element: etree._Element,
        new_element: etree._Element,
    ) -> None:
        """
        Insert *new_element* as the next sibling of *ref_element*
        under *parent*, preserving any tail text on *ref_element*.
        """
        index = list(parent).index(ref_element)
        # Transfer tail text so it stays in the correct position
        if ref_element.tail:
            new_element.tail = ref_element.tail
            ref_element.tail = None
        parent.insert(index + 1, new_element)

    def _insert_before_element(
        self,
        parent: etree._Element,
        ref_element: etree._Element,
        new_element: etree._Element,
    ) -> None:
        """
        Insert *new_element* immediately before *ref_element* under *parent*.
        """
        index = list(parent).index(ref_element)
        parent.insert(index, new_element)

    def remove_existing_markers(self, spine_name: str | None = None) -> int:
        """
        Remove any existing ``epub:type="pagebreak"`` spans from
        spine documents.

        :param spine_name: If provided, only process this single document.
            Otherwise process all spine documents.
        :return: Number of markers removed.
        """
        if spine_name:
            names = [spine_name]
        else:
            spine = getattr(self.container, 'spine_names', None) or getattr(self.container, 'spine_items', [])
            names = [item[0] if isinstance(item, tuple) else item for item in spine]

        ns = {'epub': EPUB_OPS_NS, 'xhtml': XHTML_NS}
        removed = 0

        for name in names:
            tree = self.container.parsed(name)
            modified = False

            spans = tree.xpath(
                '//xhtml:span[@epub:type="pagebreak"]',
                namespaces=ns,
            )

            for span in spans:
                parent = span.getparent()
                if parent is None:
                    continue
                # Preserve tail text by transferring it
                if span.tail:
                    prev = span.getprevious()
                    if prev is not None:
                        prev.tail = (prev.tail or '') + span.tail
                    else:
                        parent.text = (parent.text or '') + span.tail
                parent.remove(span)
                modified = True
                removed += 1

            if modified:
                self.container.dirty(name)

        return removed
