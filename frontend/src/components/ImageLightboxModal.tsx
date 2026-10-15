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
        background: "rgba(15, 23, 42, 0.85)",
        backdropFilter: "blur(6px)",
        WebkitBackdropFilter: "blur(6px)",
        display: "flex",
        flexDirection: "column",
        userSelect: "none",
        animation: "fadeIn 200ms ease",
      }}
    >
      {/* Top Header / Info Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "16px 24px",
          background: "rgba(15, 23, 42, 0.65)",
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.12)",
          color: "#ffffff",
          zIndex: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px", minWidth: 0 }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "rgba(16, 185, 129, 0.2)",
              border: "1px solid rgba(16, 185, 129, 0.4)",
              color: "#34d399",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </div>
          <div style={{ minWidth: 0 }}>
            <span style={{ fontSize: "14px", fontWeight: 600, color: "#f8fafc", display: "block", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {caption || altText || "Xem chi tiết sơ đồ kỹ thuật"}
            </span>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>
              Cuộn chuột để phóng to/thu nhỏ • Kéo chuột để di chuyển
            </span>
          </div>
        </div>

        {/* Top Right Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Đóng trình xem ảnh"
          title="Đóng trình xem ảnh (Esc)"
          style={{
            background: "rgba(255, 255, 255, 0.1)",
            border: "1px solid rgba(255, 255, 255, 0.18)",
            color: "#f8fafc",
            borderRadius: "8px",
            padding: "8px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 150ms ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.8)";
            e.currentTarget.style.borderColor = "#ef4444";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.1)";
            e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.18)";
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
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
            maxWidth: "88%",
            maxHeight: "80%",
            objectFit: "contain",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
            borderRadius: "12px",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            backgroundColor: "#0f172a",
          }}
        />
      </div>

      {/* Floating Control Dock at Bottom (Glassmorphism) */}
      <div
        style={{
          position: "fixed",
          bottom: "28px",
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "8px 16px",
          borderRadius: "9999px",
          background: "rgba(30, 41, 59, 0.75)",
          backdropFilter: "blur(14px)",
          WebkitBackdropFilter: "blur(14px)",
          border: "1px solid rgba(255, 255, 255, 0.18)",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.45), 0 8px 10px -6px rgba(0, 0, 0, 0.3)",
          zIndex: 30,
        }}
      >
        {/* Zoom Out Button */}
        <button
          type="button"
          onClick={handleZoomOut}
          title="Thu nhỏ (-)"
          aria-label="Thu nhỏ ảnh sơ đồ kỹ thuật"
          disabled={scale <= 0.5}
          style={{
            background: "rgba(255, 255, 255, 0.12)",
            color: "#ffffff",
            border: "1px solid rgba(255, 255, 255, 0.2)",
            borderRadius: "9999px",
            width: "36px",
            height: "36px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "16px",
            fontWeight: "bold",
            cursor: scale <= 0.5 ? "not-allowed" : "pointer",
            opacity: scale <= 0.5 ? 0.4 : 1,
            transition: "all 150ms ease",
          }}
          onMouseEnter={(e) => {
            if (scale > 0.5) e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.25)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.12)";
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </button>

        {/* Zoom percentage badge */}
        <div
          style={{
            fontSize: "13px",
            fontWeight: 700,
            color: "#ffffff",
            padding: "4px 10px",
            borderRadius: "9999px",
            background: "rgba(255, 255, 255, 0.12)",
            minWidth: "52px",
            textAlign: "center",
            letterSpacing: "0.02em",
          }}
        >
          {Math.round(scale * 100)}%
        </div>

        {/* Zoom In Button */}
        <button
          type="button"
          onClick={handleZoomIn}
          title="Phóng to (+)"
          aria-label="Phóng to ảnh sơ đồ kỹ thuật"
          disabled={scale >= 3.0}
          style={{
            background: "rgba(255, 255, 255, 0.12)",
            color: "#ffffff",
            border: "1px solid rgba(255, 255, 255, 0.2)",
            borderRadius: "9999px",
            width: "36px",
            height: "36px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "16px",
            fontWeight: "bold",
            cursor: scale >= 3.0 ? "not-allowed" : "pointer",
            opacity: scale >= 3.0 ? 0.4 : 1,
            transition: "all 150ms ease",
          }}
          onMouseEnter={(e) => {
            if (scale < 3.0) e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.25)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.12)";
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </button>

        {/* Divider */}
        <div style={{ width: "1px", height: "20px", background: "rgba(255, 255, 255, 0.2)", margin: "0 2px" }} />

        {/* Reset Zoom Button */}
        <button
          type="button"
          onClick={handleResetZoom}
          title="Đặt lại kích thước ban đầu (1:1)"
          aria-label="Đặt lại kích thước ban đầu"
          style={{
            background: "rgba(255, 255, 255, 0.12)",
            color: "#ffffff",
            border: "1px solid rgba(255, 255, 255, 0.2)",
            borderRadius: "9999px",
            padding: "6px 12px",
            fontSize: "13px",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            transition: "all 150ms ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.25)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.12)";
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
            <path d="M3 3v5h5"></path>
          </svg>
          1:1
        </button>

        {/* Divider */}
        <div style={{ width: "1px", height: "20px", background: "rgba(255, 255, 255, 0.2)", margin: "0 2px" }} />

        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          title="Đóng (Esc)"
          aria-label="Đóng trình xem ảnh"
          style={{
            background: "rgba(220, 38, 38, 0.8)",
            color: "#ffffff",
            border: "1px solid rgba(239, 68, 68, 0.8)",
            borderRadius: "9999px",
            padding: "6px 14px",
            fontSize: "13px",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            transition: "all 150ms ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "#dc2626";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "rgba(220, 38, 38, 0.8)";
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
          Đóng
        </button>
      </div>
    </div>
  );
}
