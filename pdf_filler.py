from pypdf import PdfReader, PdfWriter

reader = PdfReader("samples/Form297_Rev0413_Fillable.pdf")
writer = PdfWriter()

page = reader.pages[3]
fields = reader.get_fields()

writer.append(reader)

writer.update_page_form_field_values(
    writer.pages[3],
    {"txtFirstName": "HOMER"},
    auto_regenerate=False,
)

with open("samples/filled/Form297_Rev0413_Completed.pdf", "wb") as output_stream:
    writer.write(output_stream)