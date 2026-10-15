"""Multimodal document image extraction and page rendering service.

Extracts embedded images and renders scanned pages to provide visual evidence
for engineering and logistics technical documents.
"""
from dataclasses import dataclass
import io
import logging
import os
import uuid
from typing import Optional
from uuid import UUID
from PIL import Image

logger = logging.getLogger("rag.image_extractor")


@dataclass
class ExtractedImageData:
    """Metadata and storage information for an extracted document image."""
    image_id: UUID
    dataset_id: UUID
    source_version_id: UUID
    page_number: Optional[int]
    image_type: str  # "embedded" or "rendered_page"
    storage_path: str
    mime_type: str
    width: int
    height: int
    size_bytes: int
    caption: Optional[str] = None


class ImageExtractor:
    """Extracts embedded images and fallback page renders from PDF and DOCX files."""

    MAX_IMAGES_PER_DOCUMENT = 50
    MIN_DIMENSION = 64
    MAX_DIMENSION = 1600
    FALLBACK_TEXT_THRESHOLD = 50  # Character count under which a PDF page is considered scan/image-only

    def __init__(
        self,
        max_images: int = MAX_IMAGES_PER_DOCUMENT,
        min_dimension: int = MIN_DIMENSION,
        max_dimension: int = MAX_DIMENSION,
    ) -> None:
        self.max_images = max_images
        self.min_dimension = min_dimension
        self.max_dimension = max_dimension

    def _optimize_and_save(
        self,
        img: Image.Image,
        image_type: str,
        page_number: Optional[int],
        dataset_id: UUID,
        source_version_id: UUID,
        output_dir: str,
    ) -> Optional[ExtractedImageData]:
        """Tối ưu kích thước, chuẩn hóa và lưu ảnh ra đĩa dưới dạng PNG."""
        try:
            os.makedirs(output_dir, exist_ok=True)
            image_id = uuid.uuid4()
            target_path = os.path.join(output_dir, f"{image_id}.png")

            # Chuẩn hóa mode nếu cần
            if img.mode not in ("RGB", "RGBA", "L"):
                img = img.convert("RGBA" if "A" in img.mode else "RGB")

            # Giới hạn kích thước tối đa 1600px giữ nguyên tỷ lệ khung hình
            if img.width > self.max_dimension or img.height > self.max_dimension:
                img.thumbnail((self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS)

            img.save(target_path, format="PNG", optimize=True)
            size_bytes = os.path.getsize(target_path)

            caption = f"Trang {page_number}" if page_number is not None else None

            return ExtractedImageData(
                image_id=image_id,
                dataset_id=dataset_id,
                source_version_id=source_version_id,
                page_number=page_number,
                image_type=image_type,
                storage_path=target_path,
                mime_type="image/png",
                width=img.width,
                height=img.height,
                size_bytes=size_bytes,
                caption=caption,
            )
        except Exception as exc:
            logger.warning("Lỗi tối ưu hoặc lưu ảnh: %s", exc)
            return None

    def extract_from_pdf(
        self,
        content: bytes,
        dataset_id: UUID,
        source_version_id: UUID,
        output_dir: str,
    ) -> list[ExtractedImageData]:
        """Trích xuất ảnh nhúng hoặc render trang scan từ nội dung PDF."""
        import pypdfium2 as pdfium

        if not content:
            return []

        results: list[ExtractedImageData] = []
        try:
            pdf_doc = pdfium.PdfDocument(io.BytesIO(content))
        except Exception as exc:
            logger.warning("Không thể mở tài liệu PDF để trích xuất ảnh: %s", exc)
            return []

        num_pages = len(pdf_doc)
        for page_idx in range(num_pages):
            if len(results) >= self.max_images:
                logger.info("Đã đạt giới hạn tối đa %d ảnh cho tài liệu", self.max_images)
                break

            page_num = page_idx + 1
            try:
                page = pdf_doc[page_idx]
            except Exception as exc:
                logger.warning("Không thể đọc trang %d: %s", page_num, exc)
                continue

            # Kiểm tra lượng selectable text trên trang
            page_text = ""
            try:
                textpage = page.get_textpage()
                page_text = textpage.get_text_range().strip()
            except Exception:
                page_text = ""

            # Thu thập các hình ảnh nhúng (embedded images)
            embedded_pil_images: list[Image.Image] = []
            try:
                for obj in page.get_objects():
                    if isinstance(obj, pdfium.PdfImage):
                        try:
                            bm = obj.get_bitmap()
                            pil_img = bm.to_pil()
                            if (
                                pil_img.width >= self.min_dimension
                                and pil_img.height >= self.min_dimension
                            ):
                                embedded_pil_images.append(pil_img)
                        except Exception as obj_err:
                            logger.debug("Không thể trích xuất bitmap từ PdfImage: %s", obj_err)
            except Exception as scan_err:
                logger.debug("Lỗi duyệt objects trên trang %d: %s", page_num, scan_err)

            # Quyết định: Fallback render toàn trang scan (D-02) hoặc lưu embedded images
            if embedded_pil_images and len(page_text) >= self.FALLBACK_TEXT_THRESHOLD:
                # Trang bình thường có nhiều text và các sơ đồ nhúng
                for p_img in embedded_pil_images:
                    if len(results) >= self.max_images:
                        break
                    extracted = self._optimize_and_save(
                        p_img,
                        image_type="embedded",
                        page_number=page_num,
                        dataset_id=dataset_id,
                        source_version_id=source_version_id,
                        output_dir=output_dir,
                    )
                    if extracted:
                        results.append(extracted)
            elif len(page_text) < self.FALLBACK_TEXT_THRESHOLD:
                # Trang scan hoặc chụp màn hình: render toàn bộ trang chất lượng cao (150-200 DPI scale 2.0)
                try:
                    rendered_page = page.render(scale=2.0).to_pil()
                    extracted = self._optimize_and_save(
                        rendered_page,
                        image_type="rendered_page",
                        page_number=page_num,
                        dataset_id=dataset_id,
                        source_version_id=source_version_id,
                        output_dir=output_dir,
                    )
                    if extracted:
                        results.append(extracted)
                except Exception as render_err:
                    logger.warning("Lỗi render trang scan %d: %s", page_num, render_err)
                    # Thử lưu embedded image nếu render trang thất bại
                    for p_img in embedded_pil_images:
                        if len(results) >= self.max_images:
                            break
                        extracted = self._optimize_and_save(
                            p_img,
                            image_type="embedded",
                            page_number=page_num,
                            dataset_id=dataset_id,
                            source_version_id=source_version_id,
                            output_dir=output_dir,
                        )
                        if extracted:
                            results.append(extracted)
            else:
                # Có text đầy đủ và có ảnh nhúng
                for p_img in embedded_pil_images:
                    if len(results) >= self.max_images:
                        break
                    extracted = self._optimize_and_save(
                        p_img,
                        image_type="embedded",
                        page_number=page_num,
                        dataset_id=dataset_id,
                        source_version_id=source_version_id,
                        output_dir=output_dir,
                    )
                    if extracted:
                        results.append(extracted)

        return results

    def extract_from_docx(
        self,
        content: bytes,
        dataset_id: UUID,
        source_version_id: UUID,
        output_dir: str,
    ) -> list[ExtractedImageData]:
        """Trích xuất các file hình ảnh nhúng từ tệp DOCX (word/media/)."""
        import zipfile

        if not content:
            return []

        results: list[ExtractedImageData] = []
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                media_files = sorted(
                    [
                        n
                        for n in z.namelist()
                        if n.startswith("word/media/")
                        and any(
                            n.lower().endswith(ext)
                            for ext in (".png", ".jpeg", ".jpg", ".webp", ".bmp", ".tif", ".tiff")
                        )
                    ]
                )

                for name in media_files:
                    if len(results) >= self.max_images:
                        logger.info("Đã đạt giới hạn tối đa %d ảnh cho DOCX", self.max_images)
                        break

                    try:
                        img_bytes = z.read(name)
                        img = Image.open(io.BytesIO(img_bytes))

                        # Bỏ qua icon hoặc bullet quá nhỏ
                        if (
                            img.width < self.min_dimension
                            or img.height < self.min_dimension
                        ):
                            continue

                        extracted = self._optimize_and_save(
                            img,
                            image_type="embedded",
                            page_number=None,
                            dataset_id=dataset_id,
                            source_version_id=source_version_id,
                            output_dir=output_dir,
                        )
                        if extracted:
                            results.append(extracted)
                    except Exception as item_err:
                        logger.debug("Không thể mở tệp media DOCX %s: %s", name, item_err)
        except Exception as exc:
            logger.warning("Không thể đọc tệp DOCX như zip archive: %s", exc)

        return results

    def extract_images(
        self,
        content: bytes,
        file_name: str,
        dataset_id: UUID,
        source_version_id: UUID,
        output_dir: str,
    ) -> list[ExtractedImageData]:
        """Tự động phát hiện định dạng tệp và thực hiện trích xuất ảnh."""
        ext = os.path.splitext(file_name)[1].lower()
        if ext == ".pdf":
            return self.extract_from_pdf(content, dataset_id, source_version_id, output_dir)
        elif ext == ".docx":
            return self.extract_from_docx(content, dataset_id, source_version_id, output_dir)
        return []
