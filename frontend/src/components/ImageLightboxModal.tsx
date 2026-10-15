"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

export interface ImageLightboxModalProps {
  isOpen: boolean;
  imageUrl: string;
  altText?: string;
  caption?: string;
  onClose: () => void;
}

export function ImageLightboxModal({
  isOpen,
  imageUrl,
  altText = "Hình ảnh chi tiết",
  caption,
  onClose,
}: ImageLightboxModalProps) {
  const [scale, setScale] = useState<number>(1.0);
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Reset scale and position whenever modal opens or image changes
  useEffect(() => {
    if (isOpen) {
      setScale(1.0);
      setPosition({ x: 0, y: 0 });
      setIsDragging(false);
    }
  }, [isOpen, imageUrl]);

  // Lock body scroll while modal is open
  useEffect(() => {
    if (!isOpen) return;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen]);

  // Handle ESC key to close
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  const handleZoomIn = useCallback(() => {
    setScale((prev) => Math.min(3.0, Number((prev + 0.25).toFixed(2))));
  }, []);

  const handleZoomOut = useCallback(() => {
    setScale((prev) => Math.max(0.5, Number((prev - 0.25).toFixed(2))));
  }, []);

  const handleResetZoom = useCallback(() => {
    setScale(1.0);
    setPosition({ x: 0, y: 0 });
  }, []);

  // Handle mouse wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      handleZoomIn();
    } else {
      handleZoomOut();
    }
  };

  // Dragging / panning handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only left click
    setIsDragging(true);
    dragStartRef.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStartRef.current.x,
      y: e.clientY - dragStartRef.current.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  if (!isOpen || !imageUrl) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Xem hình ảnh kích thước lớn"
      onClick={(e) => {
        // Close if clicked directly on the outer backdrop
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(15, 23, 42, 0.88)",
        display: "flex",
        flexDirection: "column",
        userSelect: "none",
      }}
    >
      {/* Top Header / Toolbar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 24px",
          background: "rgba(15, 23, 42, 0.75)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.12)",
          color: "#ffffff",
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px", minWidth: 0 }}>
          <span style={{ fontSize: "14px", fontWeight: "bold", color: "#f8fafc", whiteSpace: "nowrap" }}>
            🔍 Xem chi tiết sơ đồ / hình ảnh
          </span>
          <span
            style={{
              fontSize: "12px",
              background: "rgba(255, 255, 255, 0.15)",
              padding: "2px 8px",
              borderRadius: "4px",
              color: "#cbd5e1",
            }}
          >
            {Math.round(scale * 100)}%
          </span>
        </div>

        {/* Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            type="button"
            onClick={handleZoomIn}
            title="Phóng to (+)"
            aria-label="Phóng to"
            disabled={scale >= 3.0}
            style={{
              background: "rgba(255, 255, 255, 0.12)",
              color: "#ffffff",
              border: "1px solid rgba(255, 255, 255, 0.25)",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "14px",
              fontWeight: "bold",
              cursor: scale >= 3.0 ? "not-allowed" : "pointer",
              opacity: scale >= 3.0 ? 0.5 : 1,
            }}
          >
            + Phóng to
          </button>
          <button
            type="button"
            onClick={handleZoomOut}
            title="Thu nhỏ (-)"
            aria-label="Thu nhỏ"
            disabled={scale <= 0.5}
            style={{
              background: "rgba(255, 255, 255, 0.12)",
              color: "#ffffff",
              border: "1px solid rgba(255, 255, 255, 0.25)",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "14px",
              fontWeight: "bold",
              cursor: scale <= 0.5 ? "not-allowed" : "pointer",
              opacity: scale <= 0.5 ? 0.5 : 1,
            }}
          >
            - Thu nhỏ
          </button>
          <button
            type="button"
            onClick={handleResetZoom}
            title="Đặt lại tỉ lệ (1:1)"
            aria-label="Đặt lại kích thước gốc"
            style={{
              background: "rgba(255, 255, 255, 0.12)",
              color: "#ffffff",
              border: "1px solid rgba(255, 255, 255, 0.25)",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            1:1 Gốc
          </button>
          <button
            type="button"
            onClick={onClose}
            title="Đóng (Esc)"
            aria-label="Đóng cửa sổ xem ảnh"
            style={{
              background: "#dc2626",
              color: "#ffffff",
              border: "1px solid #b91c1c",
              borderRadius: "6px",
              padding: "6px 14px",
              fontSize: "14px",
              fontWeight: "bold",
              cursor: "pointer",
              marginLeft: "8px",
            }}
          >
            ✕ Đóng
          </button>
        </div>
      </div>

      {/* Main Viewport Container */}
      <div
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{
          flex: 1,
          position: "relative",
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: isDragging ? "grabbing" : scale > 1.0 ? "grab" : "default",
        }}
      >
        <img
          src={imageUrl}
          alt={altText}
          draggable={false}
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            transformOrigin: "center center",
            transition: isDragging ? "none" : "transform 0.12s ease-out",
            maxWidth: "90%",
            maxHeight: "85%",
            objectFit: "contain",
            boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
            borderRadius: "6px",
            backgroundColor: "#0f172a",
          }}
        />
      </div>

      {/* Bottom Information & Guide Bar */}
      <div
        style={{
          padding: "10px 24px",
          background: "rgba(15, 23, 42, 0.85)",
          borderTop: "1px solid rgba(255, 255, 255, 0.1)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          color: "#cbd5e1",
          fontSize: "12px",
          zIndex: 10,
        }}
      >
        <div style={{ maxWidth: "60%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {caption || altText ? (
            <span>
              <strong style={{ color: "#f8fafc" }}>Thông tin:</strong> {caption || altText}
            </span>
          ) : (
            <span>Tài liệu trích dẫn</span>
          )}
        </div>
        <div style={{ color: "#94a3b8" }}>
          💡 Mẹo: Cuộn chuột để phóng to/thu nhỏ • Nhấn giữ và kéo chuột để di chuyển
        </div>
      </div>
    </div>
  );
}
