"""
XML Reviser for python-docx
Helper class to inject OpenXML revision marks (track changes) and comments.
"""
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import time
import datetime

class XmlReviser:
    """Helper to manipulate underlying XML for track changes and comments."""
    
    def __init__(self, doc):
        self.doc = doc
        self.author = "DocAI"
        self.date_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def enable_track_revisions(self):
        """Enable track revisions in settings.xml and configure view to show revisions."""
        settings = self.doc.settings.element
        
        # 1. Add w:trackRevisions element to enable tracking
        track_revisions = settings.find(qn('w:trackRevisions'))
        if track_revisions is None:
            track_revisions = OxmlElement('w:trackRevisions')
            settings.append(track_revisions)
        
        # Explicitly set w:val="true" to ensure it's enabled
        track_revisions.set(qn('w:val'), 'true')
        
        # 2. Add w:revisionView element to control what revisions are displayed
        # This ensures Word automatically shows revision marks when opening the document
        revision_view = settings.find(qn('w:revisionView'))
        if revision_view is None:
            revision_view = OxmlElement('w:revisionView')
            settings.append(revision_view)
        
        # Enable display of insertions and deletions
        revision_view.set(qn('w:ins'), 'true')  # Show insertions
        revision_view.set(qn('w:del'), 'true')  # Show deletions
        revision_view.set(qn('w:formatting'), 'true')  # Show formatting changes
        revision_view.set(qn('w:markup'), 'true')  # Show all markup
        
        # Note: With revisionView configured, Word should automatically display
        # revision marks when opening the document, without requiring manual
        # "Show Markup" activation in the Review tab.

    def add_comment(self, paragraph, text, author="DocAI", initials="AI"):
        """
        Add a native Word comment to the paragraph.

        NOTE: Since python-docx does not support native comments easily, and injecting XML manually
        is risky and complex (requires managing relationships and comments.xml part),
        we abide by the user's request to NOT pollute the document text with inline suggestions.

        So for now, this is a NO-OP. We only perform structural fixes (revisions).
        Future improvement: Implement robust XML injection for native comments.
        """
        pass

    def mark_run_as_inserted(self, run):
        """Wrap a run in <w:ins> to show as inserted text."""
        r = run._r
        parent = r.getparent()
        
        # Create w:ins element
        ins = OxmlElement('w:ins')
        ins.set(qn('w:id'), str(int(time.time() * 1000) % 2**31)) # Random ID
        ins.set(qn('w:author'), self.author)
        ins.set(qn('w:date'), self.date_str)
        
        # Replace run with ins containing run
        parent.replace(r, ins)
        ins.append(r)

    def mark_paragraph_property_change(self, paragraph):
        """
        Mark paragraph properties as changed.
        This requires <w:pPrChange> inside <w:pPr>.
        """
        pPr = paragraph._p.get_or_add_pPr()
        
        # Create pPrChange
        pPrChange = OxmlElement('w:pPrChange')
        pPrChange.set(qn('w:id'), str(int(time.time() * 1000) % 2**31))
        pPrChange.set(qn('w:author'), self.author)
        pPrChange.set(qn('w:date'), self.date_str)
        
        # It needs a child w:pPr which represents the OLD state.
        # For simplicity, we create an empty old pPr (implying "whatever it was before")
        old_pPr = OxmlElement('w:pPr')
        pPrChange.append(old_pPr)
        
        pPr.append(pPrChange)

    def set_page_margin(self, top_mm, bottom_mm, left_mm, right_mm):
        """Set page margins and mark as revision (sectPrChange)."""
        sections = self.doc.sections
        for section in sections:
            # Update values
            from docx.shared import Mm
            section.top_margin = Mm(top_mm)
            section.bottom_margin = Mm(bottom_mm)
            section.left_margin = Mm(left_mm)
            section.right_margin = Mm(right_mm)
            
            # Mark revision on sectPr
            sectPr = section._sectPr
            sectPrChange = OxmlElement('w:sectPrChange')
            sectPrChange.set(qn('w:id'), str(int(time.time() * 1000) % 2**31))
            sectPrChange.set(qn('w:author'), self.author)
            sectPrChange.set(qn('w:date'), self.date_str)
            sectPr.append(sectPrChange)

    def set_paragraph_indent(self, paragraph, first_line_chars):
        """Set first line indent using character units (1/100th char)."""
        # Correct approach: w:ind w:firstLineChars="200" (units of 1/100th char)
        pPr = paragraph._p.get_or_add_pPr()
        ind = pPr.find(qn('w:ind'))
        if ind is None:
            ind = OxmlElement('w:ind')
            pPr.append(ind)
            
        # Remove specific length attributes to avoid conflict if we can use chars
        if qn('w:firstLine') in ind.attrib:
            del ind.attrib[qn('w:firstLine')]
            
        # Set firstLineChars (200 = 2.00 chars)
        ind.set(qn('w:firstLineChars'), str(int(first_line_chars * 100)))
        
        self.mark_paragraph_property_change(paragraph)

    def set_heading_style(self, paragraph, font_name, size_pt, alignment, bold=True):
        """Set heading style properties."""
        from docx.shared import Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # 1. Alignment
        if alignment == "center":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif alignment == "left":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            
        # 2. Font properties (need to apply to all runs in paragraph)
        for run in paragraph.runs:
            run.font.name = font_name
            # For Chinese fonts in Word, we need to set eastAsia attribute
            rPr = run._r.get_or_add_rPr()
            rFonts = rPr.find(qn('w:rFonts'))
            if rFonts is None:
                rFonts = OxmlElement('w:rFonts')
                rPr.append(rFonts)
            rFonts.set(qn('w:eastAsia'), font_name)
            
            # 3. Size (handle complex script size for Chinese)
            # w:sz is for ASCII/Latin, w:szCs is for Complex Script (Chinese)
            # Both units are half-points
            size_half_pts = int(size_pt * 2)
            
            sz = rPr.find(qn('w:sz'))
            if sz is None:
                sz = OxmlElement('w:sz')
                rPr.append(sz)
            sz.set(qn('w:val'), str(size_half_pts))
            
            szCs = rPr.find(qn('w:szCs'))
            if szCs is None:
                szCs = OxmlElement('w:szCs')
                rPr.append(szCs)
            szCs.set(qn('w:val'), str(size_half_pts))
            
            # Update python-docx object wrapper to reflect change (optional but good for consistency)
            # run.font.size = Pt(size_pt) # This only sets w:sz usually
            
            run.font.bold = bold
            
            # Mark run revision (rPrChange)
            rPrChange = OxmlElement('w:rPrChange')
            rPrChange.set(qn('w:id'), str(int(time.time() * 1000) % 2**31))
            rPrChange.set(qn('w:author'), self.author)
            rPrChange.set(qn('w:date'), self.date_str)
            rPrChange.append(OxmlElement('w:rPr')) # Empty old state
            rPr.append(rPrChange)

        self.mark_paragraph_property_change(paragraph)

    def replace_text_in_run(self, run, old_text, new_text):
        """
        Replace text within a specific run with track changes.
        Marks the old text as deleted and new text as inserted.
        """
        if old_text not in run.text:
            return False

        # Get the run element
        r = run._r
        parent = r.getparent()
        run_index = parent.index(r)

        # Copy run properties
        rPr = r.find(qn('w:rPr'))

        # Create deleted run (original text with error)
        del_run = OxmlElement('w:r')
        if rPr is not None:
            del_run.append(rPr.__copy__())
        del_t = OxmlElement('w:t')
        del_t.set(qn('xml:space'), 'preserve')
        del_t.text = run.text
        del_run.append(del_t)

        # Wrap in w:del - this returns the w:del element containing del_run
        del_wrapper = self._wrap_as_deleted(del_run)

        # Create inserted run (corrected text)
        ins_run = OxmlElement('w:r')
        if rPr is not None:
            ins_run.append(rPr.__copy__())
        ins_t = OxmlElement('w:t')
        ins_t.set(qn('xml:space'), 'preserve')
        ins_t.text = run.text.replace(old_text, new_text)
        ins_run.append(ins_t)

        # Wrap in w:ins - this returns the w:ins element containing ins_run
        ins_wrapper = self._wrap_as_inserted(ins_run)

        # Replace original run with revision wrappers
        parent.remove(r)
        parent.insert(run_index, ins_wrapper)
        parent.insert(run_index, del_wrapper)

        return True

    def _wrap_as_deleted(self, element):
        """Wrap an element in w:del for track changes."""
        del_elem = OxmlElement('w:del')
        del_elem.set(qn('w:id'), str(int(time.time() * 1000) % 2**31))
        del_elem.set(qn('w:author'), self.author)
        del_elem.set(qn('w:date'), self.date_str)
        del_elem.append(element)
        return del_elem

    def _wrap_as_inserted(self, element):
        """Wrap an element in w:ins for track changes."""
        ins = OxmlElement('w:ins')
        ins.set(qn('w:id'), str(int(time.time() * 1000) % 2**31))
        ins.set(qn('w:author'), self.author)
        ins.set(qn('w:date'), self.date_str)
        ins.append(element)
        return ins

    def replace_text_in_paragraph(self, paragraph, old_text, new_text):
        """
        Replace text in a paragraph with track changes enabled.
        Searches through all runs to find and replace the text.
        """
        if old_text not in paragraph.text:
            return False

        # Find the run containing the old text
        for run in paragraph.runs:
            if old_text in run.text:
                return self.replace_text_in_run(run, old_text, new_text)

        return False

