from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import math
from state import State
from langchain_core.runnables import RunnableConfig

class AcquaintanceGraph(Flowable):
    """Rysuje graf znajomości w układzie kołowym."""
    def __init__(self, agents, edges, width=16*cm, height=10*cm):
        super().__init__()
        self.agents = agents
        self.edges = edges
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        center_x = self.width / 2
        center_y = self.height / 2
        radius = min(center_x, center_y) * 0.7
        pos = {}
        for i, agent in enumerate(self.agents):
            angle = 2 * math.pi * i / len(self.agents)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            pos[agent] = (x, y)

        c.setLineWidth(1)
        c.setStrokeColor(colors.HexColor("#2e6da4"))
        for frm, to in self.edges:
            if frm in pos and to in pos:
                x1, y1 = pos[frm]; x2, y2 = pos[to]
                c.line(x1, y1, x2, y2)
                dx, dy = x2 - x1, y2 - y1
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    ux, uy = dx/dist, dy/dist
                    c.circle(x2 - ux*15 + uy*3, y2 - uy*15 - ux*3, 1, fill=1)

        for name, (x, y) in pos.items():
            c.setFillColor(colors.HexColor("#1a3a5c"))
            c.circle(x, y, 12, fill=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(x, y + 15, name)

class GaiaPDFGenerator:
    def __init__(self, output_path, data):
        self.path = output_path
        self.data = data
        self.styles = self._get_base_styles()

    def _get_base_styles(self):
        return {
            'title': ParagraphStyle('T', fontSize=22, fontName='Helvetica-Bold', textColor=colors.HexColor("#1a3a5c"), alignment=TA_CENTER, spaceAfter=12),
            'h1': ParagraphStyle('H1', fontSize=16, fontName='Helvetica-Bold', textColor=colors.white, backColor=colors.HexColor("#1a3a5c"), leftIndent=-10, rightIndent=-10, borderPadding=6, spaceBefore=12, spaceAfter=10),
            'h2': ParagraphStyle('H2', fontSize=13, fontName='Helvetica-Bold', textColor=colors.HexColor("#1a3a5c"), spaceBefore=10, spaceAfter=6),
            'body': ParagraphStyle('B', fontSize=10, fontName='Helvetica', alignment=TA_JUSTIFY, leading=13),
            'th': ParagraphStyle('TH', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_CENTER),
            'td': ParagraphStyle('TD', fontSize=7.5, fontName='Helvetica', leading=9),
            'td_code': ParagraphStyle('TDC', fontSize=7, fontName='Courier', leading=8),
        }

    def _create_table(self, data, col_widths):
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2e6da4")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#2e6da4")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return t

    def generate(self):
        story = []
        doc = SimpleDocTemplate(self.path, pagesize=A4, margin=(1*cm, 1*cm, 1*cm, 1*cm))

        # Strona tytułowa
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph(self.data.get('title', 'DOKUMENTACJA GAIA'), self.styles['title']))
        story.append(HRFlowable(width="100%", color=colors.HexColor("#2e6da4")))
        
        # 1. Opis
        story.append(Paragraph("1. Opis i Wymagania", self.styles['h1']))
        story.append(Paragraph(self.data.get('description', ''), self.styles['body']))
        for req in self.data.get('requirements', []):
            story.append(Paragraph(f"&bull; {req}", self.styles['body']))

        # 2. Role (Zastosowanie <br/> dla nowej linii)
        story.append(PageBreak())
        story.append(Paragraph("2. Model Ról", self.styles['h1']))
        for r in self.data.get('roles', []):
            data = [
                [Paragraph(f"Role: <b>{r['name']}</b>", self.styles['th']), ""],
                ["Description", Paragraph(r['description'], self.styles['td'])],
                ["Responsibilities", Paragraph(r['responsibilities'], self.styles['td'])],
                ["Permissions", Paragraph(r['permissions'], self.styles['td_code'])],
                ["Activities", Paragraph(", ".join(r['activities']), self.styles['td'])],
                ["Protocols", Paragraph(", ".join(r['protocols']), self.styles['td'])],
            ]
            t = self._create_table(data, [4*cm, 15*cm])
            t.setStyle(TableStyle([('SPAN', (0,0), (1,0)), ('BACKGROUND', (0,1), (0,-5), colors.HexColor("#e8f0fa"))]))
            story.append(KeepTogether([t, Spacer(1, 15)]))

        # 3. Interakcje (Rozdzielone IN/OUT i Processing)
        story.append(PageBreak())
        story.append(Paragraph("3. Model Interakcji", self.styles['h1']))
        headers = ["Goal", "Name","Initiator", "Responder", "Inputs", "Outputs", "Description"]
        rows = [[Paragraph(h, self.styles['th']) for h in headers]]
        for i in self.data.get('interactions', []):
            rows.append([
                Paragraph(i['goal'], self.styles['td']),
                Paragraph(i['protocol_name'], self.styles['td']),
                Paragraph(i['initiator'], self.styles['td']),
                Paragraph(i['responder'], self.styles['td']),
                Paragraph(", ".join(i['in']), self.styles['td']),
                Paragraph(", ".join(i['out']), self.styles['td']),
                Paragraph(i['description'], self.styles['td'])
            ])
        story.append(self._create_table(rows, [3*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm, 5*cm]))

        # 4. Usługi (Pełny rozdział pól)
        story.append(PageBreak())
        story.append(Paragraph("4. Model Usług", self.styles['h1']))
        headers = ["Service", "Agent", "In/Out", "Pre/Post Condition", "Derived From"]
        rows = [[Paragraph(h, self.styles['th']) for h in headers]]
        for s in self.data.get('services', []):
            io = f"<b>IN:</b> {', '.join(s['in'])}<br/><b>OUT:</b> {', '.join(s['out'])}"
            cond = f"<b>PRE:</b> {s['pre']}<br/><b>POST:</b> {s['post']}"
            rows.append([
                Paragraph(s['name'], self.styles['td']),
                Paragraph(s['agent'], self.styles['td']),
                Paragraph(io, self.styles['td']),
                Paragraph(cond, self.styles['td_code']),
                Paragraph(s['derived'], self.styles['td'])
            ])
        story.append(self._create_table(rows, [3.5*cm, 3.5*cm, 4*cm, 5*cm, 3*cm]))

        # 5. Model Znajomości
        story.append(PageBreak())
        story.append(Paragraph("5. Model Znajomości", self.styles['h1']))
        agents = [a['name'] for a in self.data.get('agents', [])]
        story.append(AcquaintanceGraph(agents, self.data.get('acquaintances', [])))
        
        doc.build(story)
        
        
def process_documentation(state: State, config: RunnableConfig = None):
    configurable = config.get("metadata")
    pdf_path = configurable.get("documentation_pdf")
    
    description = state.get("description", "")
    requirements = state.get("functional_requirements", [])

    roles_mapped = []
    for r in state['roles'].roles:
        p = r.permissions
        res = r.responsibilities
        
        perm_text = (f"READ: {', '.join(p.read)}<br/>"
                     f"WRITE: {', '.join(p.write)}<br/>"
                     f"CONSUME: {', '.join(p.consume)}<br/>"
                     f"PRODUCE: {', '.join(p.produce)}")
        
        safety_text = "<br/>".join(res.safety)
        resp_text = f"<b>Liveness:</b> {res.liveness}<br/><b>Safety:</b> {safety_text}"
        
        roles_mapped.append({
            "name": r.name,
            "description": r.description,
            "activities": r.activities,
            "protocols": r.protocols,
            "permissions": perm_text,
            "responsibilities": resp_text
        })

    interactions_mapped = []
    for i in state['interactions'].interactions:
        interactions_mapped.append({
            "goal": i.goal, 
            "protocol_name": i.protocol_name,
            "initiator": i.initiator, 
            "responder": i.responder,
            "in": i.inputs, 
            "out": i.outputs,
            "description": i.description
            
        })

    services_mapped = []
    for s in state['service_model'].services:
        services_mapped.append({
            "name": s.name, 
            "agent": s.provided_by, 
            "derived": s.derived_from,
            "in": s.inputs,
            "out": s.outputs,
            "pre": s.pre_condition, 
            "post": s.post_condition
        })

    acq_edges = []
    for acq in state['acquaintance_model'].acquaintances:
        for rec in acq.receiver.split(","):
            acq_edges.append((acq.sender, rec.strip()))

    clean_data = {
        "description": description,
        "requirements": requirements,
        "roles": roles_mapped,
        "interactions": interactions_mapped,
        "services": services_mapped,
        "agents": [ {"name": a.name} for a in state['agent_model'].agent_types ],
        "acquaintances": acq_edges
    }

    GaiaPDFGenerator(pdf_path, clean_data).generate()
    
    return {
        "documentation": map_to_implementation(state)
    }
    
    
def map_to_implementation(state: State):
    documetation = f"""
    MAS DOCUMENTAION WITH GAIA METHODOLOGY\n\n
    1. System Description: {state.get("description", "")}\n
    2. Functional Requirements:\n
    {"".join([f"   - {req}\n" for req in state.get("functional_requirements", [])])}\n
    ==== GAIA ANALYSIS ====\n
    3. Roles:\n
    {state.get("roles" ).model_dump_json()}\n
    4. Interactions:\n
    {state.get("interactions").model_dump_json()}\n
    === GAIA DESIGN ====\n
    5. Agents:\n
    {state.get("agent_model").model_dump_json()}\n
    6. Services:\n
    {state.get("service_model").model_dump_json()}\n
    7. Acquaintances:\n
    {state.get("acquaintance_model").model_dump_json()}\n
    """

    print("\n"*5)
    print("==================== GENERATED DOCUMENTATION ====================")
    print(documetation)
    print("\n"*5)
    
    return documetation