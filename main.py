import OcrToTableTool as ottt
import TableExtractor as te
import TableLinesRemover as tlr
import cv2

path_to_image = "./pdf_to_image/convert_pdf_to_images/C555018250_adresses_table_300.jpg" # "./image/nutrition_table.jpg" pdfimage9 pdfimage4
table_extractor = te.TableExtractor(path_to_image)
perspective_corrected_image = table_extractor.execute()
cv2.imshow("perspective_corrected_image", perspective_corrected_image)


lines_remover = tlr.TableLinesRemover(perspective_corrected_image)
image_without_lines, image_with_lines_only, image_without_lines_white = lines_remover.execute()
cv2.imshow("image_without_lines", image_without_lines)

ocr_tool = ottt.OcrToTableTool(image_without_lines, perspective_corrected_image, image_with_lines_only, image_without_lines_white)
ocr_tool.execute()

cv2.waitKey(0)
cv2.destroyAllWindows()