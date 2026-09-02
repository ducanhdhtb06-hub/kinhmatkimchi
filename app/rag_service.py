"""
OptiStyle Pro / Kính Mắt Kim Chi - AI Medical Optometry RAG Engine
Chuyên sâu Nhãn khoa, Khúc xạ Quang học, Tư vấn Bác sĩ Mắt & Đề xuất Tròng Kính Y Khoa.
"""

import math
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# ==============================================================================
# HỆ THỐNG TRI THỨC Y KHOA & QUANG HỌC CHUYÊN SÂU (OPHTHALMOLOGY & OPTOMETRY KB)
# ==============================================================================

MEDICAL_OPTICAL_KNOWLEDGE_BASE = [
    # 1. TẬT KHÚC XẠ: CẬN THỊ & KIỂM SOÁT ĐỘ CẬN
    {
        "id": "kb_myopia_care",
        "title": "Bác sĩ tư vấn: Tật Cận Thị (Myopia) & Cách kiểm soát tăng độ cận",
        "category": "Bệnh Lý & Khúc Xạ",
        "keywords": ["cận thị", "cận", "tăng độ", "nhìn mờ", "nhìn xa", "myopia", "ortho-k", "nheo mắt", "học đường"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "**1. Cơ chế sinh học:** Cận thị xảy ra khi trục nhãn cầu dài hơn bình thường hoặc giác mạc quá cong, khiến hình ảnh hội tụ ở phía trước võng mạc thay vì rơi đúng trên hoàng điểm. Người bị cận nhìn gần rất rõ nhưng nhìn xa bị mờ và phải nheo mắt.\n\n"
            "**2. Nguyên nhân tăng độ nhanh:**\n"
            "• Nhìn màn hình máy tính/điện thoại ở cự ly quá gần (< 30cm) trong nhiều giờ liên tục.\n"
            "• Thiếu ánh sáng tự nhiên ngoài trời (ánh sáng mặt trời kích thích tiết Dopamine giúp hạn chế dài trục nhãn cầu).\n"
            "• Đeo kính không đúng số độ hoặc đeo kính lệch tâm đồng tử (lệch PD).\n\n"
            "**3. Giải pháp tròng kính tối ưu:**\n"
            "• Cận nhẹ (0.00D đến -2.50D): Chiết suất **1.56** hoặc **1.60**.\n"
            "• Cận vừa (-2.75D đến -4.50D): Chiết suất **1.60** mỏng nhẹ, độ truyền quang cao.\n"
            "• Cận cao (-4.75D đến -7.00D): Chiết suất **1.67** siêu mỏng, phẳng mặt tròng (Aspheric).\n"
            "• Cận nặng (trên -7.00D): Chiết suất **1.74** mỏng nhất thế giới, giảm thu nhỏ mắt.\n\n"
            "**4. Lời khuyên vệ sinh mắt:** Áp dụng quy tắc **20-20-20** (mỗi 20 phút nhìn gần, nhìn xa 6 mét trong 20 giây) và duy trì 1-2 giờ hoạt động ngoài trời mỗi ngày."
        )
    },

    # 2. TẬT KHÚC XẠ: LOẠN THỊ & TRỤC LOẠN
    {
        "id": "kb_astigmatism_care",
        "title": "Bác sĩ tư vấn: Tật Loạn Thị (Astigmatism) & Tầm quan trọng của Trục AXIS",
        "category": "Bệnh Lý & Khúc Xạ",
        "keywords": ["loạn thị", "loạn", "bóng mờ", "nhòe", "trục", "axis", "cyl", "nhức thái dương", "song thị"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "**1. Cơ chế sinh học:** Loạn thị xuất hiện khi bề mặt giác mạc có độ cong không đồng đều (có hình dạng giống quả bóng bầu dục thay vì hình cầu tròn hoàn hảo). Ánh sáng đi vào mắt bị bẻ cong thành nhiều tiêu điểm khác nhau, khiến hình ảnh ở mọi khoảng cách bị nhòe, viền chữ bị đổ bóng đôi hoặc lóa tia sáng ban đêm.\n\n"
            "**2. Triệu chứng lâm sàng:** Thường xuyên mỏi mắt, nhức vùng trán/thái dương sau khi đọc sách hoặc lái xe ban đêm, hay nghiêng đầu để nhìn rõ chữ.\n\n"
            "**3. Thông số đơn kính bắt buộc:**\n"
            "• **CYL (Cylinder):** Độ loạn thị (ví dụ: -0.75D, -1.25D).\n"
            "• **AXIS (Trục loạn):** Góc định hướng từ $1^\\circ$ đến $180^\\circ$. Đây là thông số tuyệt đối quan trọng; chỉ cần lệch $5^\\circ$ là mắt sẽ bị méo hình và chóng mặt.\n\n"
            "**4. Giải pháp tròng kính:** Cần chọn tròng kính có thiết kế phi cầu (Aspheric Design) hoặc tròng kính cá nhân hóa Freeform để triệt tiêu quang sai vùng biên, giúp trường nhìn phẳng và sắc nét trung thực."
        )
    },

    # 3. HỘI CHỨNG THỊ GIÁC MÀN HÌNH (CVS) & KHÔ MẮT
    {
        "id": "kb_digital_eye_strain_cvs",
        "title": "Bác sĩ tư vấn: Hội chứng Thị giác Màn hình (CVS), Mỏi mắt & Khô mắt văn phòng",
        "category": "Bệnh Lý & Khúc Xạ",
        "keywords": ["mỏi mắt", "khô mắt", "máy tính", "điện thoại", "cvs", "nhức mắt", "rát mắt", "chảy nước mắt", "đỏ mắt"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "**1. Cơ chế bệnh sinh:** Khi tập trung cao độ vào màn hình kỹ thuật số, tần số chớp mắt tự nhiên giảm từ **16-20 lần/phút xuống chỉ còn 5-7 lần/phút**. Màng phim nước mắt bay hơi nhanh khiến giác mạc bị khô rát, đỏ ngứa và mờ từng cơn.\n\n"
            "**2. Tác hại của Ánh Sáng Xanh Tím (415-455nm):** Bước sóng ngắn mang năng lượng cao xuyên sâu vào tận hoàng điểm võng mạc, gây stress oxy hóa tế bào biểu mô sắc tố và ức chế hormone Melatonin gây mất ngủ, rối loạn đồng hồ sinh học.\n\n"
            "**3. Giải pháp tròng kính y khoa:**\n"
            "• **Tròng Blue Cut / Blue UV Control:** Ngăn chặn 100% tia UV và lọc 95% ánh sáng xanh tím có hại, bảo vệ mắt khỏi hội chứng CVS.\n"
            "• **Tròng chống mỏi Relax / Eyezen:** Có vùng tăng công suất nhẹ ở đáy tròng (+0.4D đến +0.6D) hỗ trợ cơ thể mi mắt không phải điều tiết quá mức khi đọc tài liệu.\n\n"
            "**4. Phác đồ chăm sóc mắt:** Sử dụng nước mắt nhân tạo không chứa chất bảo quản (dung dịch Sodium Hyaluronate 0.1% - 0.18%) nhỏ 3-4 lần/ngày."
        )
    },

    # 4. LÃO THỊ & KÍNH ĐA TRÒNG (PROGRESSIVE LENSES)
    {
        "id": "kb_presbyopia_progressives",
        "title": "Bác sĩ tư vấn: Lão Thị sau tuổi 40 & Công nghệ Kính Đa Tròng Không Đường Biên",
        "category": "Bệnh Lý & Khúc Xạ",
        "keywords": ["lão thị", "người lớn tuổi", "đọc sách", "đa tròng", "hai tròng", "progressive", "nhìn gần mờ", "tuổi 40", "add"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "**1. Cơ chế sinh học:** Sau tuổi 40, thể thủy tinh tự nhiên trong mắt bắt đầu xơ cứng và giảm dần độ đàn hồi, khiến mắt mất khả năng điều tiết để nhìn gần. Người lão thị phải đưa điện thoại/sách báo ra xa sải tay mới đọc được chữ.\n\n"
            "**2. Kính Đa Tròng (Progressive Lenses) - Giải pháp tối ưu:**\n"
            "• Khác với kính 2 tròng cổ điển có lằn ranh ngăn cách lộ tuổi tác, Kính Đa Tròng chuyển tiếp độ mượt mà từ trên xuống dưới:\n"
            "  - Vùng trên: Nhìn xa (lái xe, ngắm cảnh).\n"
            "  - Vùng giữa: Nhìn cự ly trung bình (màn hình máy tính, bảng điều khiển ô tô).\n"
            "  - Vùng dưới: Nhìn gần (đọc sách báo, xem điện thoại).\n"
            "• Thẩm mỹ cao, trẻ trung, nhìn như kính cận thông thường.\n\n"
            "**3. Lưu ý khi mới làm quen kính đa tròng:** Trong 3-5 ngày đầu, cần tập thói quen chuyển động đầu nhẹ nhàng theo hướng nhìn thay vì chỉ liếc mắt sang góc."
        )
    },

    # 5. CHI TIẾT VỀ CHIẾT SUẤT TRÒNG KÍNH (1.56, 1.60, 1.67, 1.74)
    {
        "id": "kb_lens_index_matrix",
        "title": "Bác sĩ tư vấn: Bảng ma trận chọn Chiết Suất Tròng Kính (Refractive Index)",
        "category": "Tròng Kính Quang Học",
        "keywords": ["chiết suất", "1.56", "1.60", "1.67", "1.74", "dày", "mỏng", "nặng", "nhẹ", "trọng lượng", "viền tròng"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "Chiết suất tròng kính tỉ lệ thuận với khả năng bẻ cong ánh sáng. Chiết suất càng cao thì tròng kính càng mỏng, nhẹ và thẩm mỹ:\n\n"
            "• **Chiết suất 1.56 (Standard Index):**\n"
            "  - Phù hợp: Cận 0.00D đến -2.50D.\n"
            "  - Ưu điểm: Giá thành kinh tế, độ trong suốt cao (Abbe ~36).\n\n"
            "• **Chiết suất 1.60 (High Index MR-8):**\n"
            "  - Phù hợp: Cận -2.75D đến -4.50D.\n"
            "  - Ưu điểm: Mỏng hơn 20% so với 1.56, chất liệu MR-8 cực kỳ dẻo dai, chịu lực gấp 5 lần, bắt buộc dùng cho gọng khoan ốc hoặc xẻ cước.\n\n"
            "• **Chiết suất 1.67 (Ultra High Index MR-7):**\n"
            "  - Phù hợp: Cận -4.75D đến -7.00D.\n"
            "  - Ưu điểm: Mỏng hơn 35% so với 1.56, mép tròng mỏng phẳng, không bị dày cộm chìa ra ngoài gọng.\n\n"
            "• **Chiết suất 1.74 (Super Ultra High Index):**\n"
            "  - Phù hợp: Cận nặng trên -7.00D hoặc loạn thị cao.\n"
            "  - Ưu điểm: Đỉnh cao công nghệ quang học, mỏng hơn 45-50%, giảm triệt để hiện tượng méo hình biên và không làm mắt bị thu nhỏ khi nhìn từ ngoài vào."
        )
    },

    # 6. TRÒNG KÍNH ĐỔI MÀU (PHOTOCHROMIC / TRANSITIONS)
    {
        "id": "kb_transitions_photochromic",
        "title": "Bác sĩ tư vấn: Tròng Kính Đổi Màu Cảm Biến Tia UV (Transitions Photochromic)",
        "category": "Tròng Kính Quang Học",
        "keywords": ["đổi màu", "transitions", "ra nắng", "râm", "tia uv", "chống chói", "khói", "trà", "2 trong 1"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "**1. Nguyên lý quang hóa học:** Tròng kính chứa hàng triệu phân tử nhạy sáng (Naphthopyran). Khi tiếp xúc với bức xạ tử ngoại (Tia UV), các phân tử này mở liên kết cấu trúc và hấp thụ ánh sáng, chuyển từ trạng thái trong suốt sang màu râm mát chỉ trong **15 - 30 giây**.\n\n"
            "**2. Ưu điểm vượt trội:**\n"
            "• Giải pháp 2 trong 1: Trong nhà là kính cận trong suốt, ra ngoài trời tự biến thành kính râm có số độ.\n"
            "• Ngăn chặn 100% tia cực tím UV400 và giảm 85% cường độ ánh sáng chói lóa, phòng ngừa đục thủy tinh thể và thoái hóa hoàng điểm do nắng gắt.\n\n"
            "**3. Các tông màu thời trang y khoa:**\n"
            "• Xám Khói (Grey): Trung thực màu sắc nhất, thích hợp cho mọi nhu cầu.\n"
            "• Nâu Trà (Brown): Tăng cường độ tương phản, rất dịu mắt cho người hay đi ô tô/lái xe.\n"
            "• Xanh Rêu (Graphite Green): Cực kỳ sang trọng và làm dịu mắt trong điều kiện ánh sáng gay gắt."
        )
    },

    # 7. CHỌN GỌNG THEO TỶ LỆ KHUÔN MẶT (FACE SHAPE ANATOMY)
    {
        "id": "kb_face_shape_anatomy",
        "title": "Bác sĩ tư vấn: Nhân trắc học khuôn mặt & Lựa chọn dáng gọng kính tôn diện mạo",
        "category": "Gọng Kính & Nhân Trắc Học",
        "keywords": ["mặt tròn", "mặt vuông", "mặt trái xoan", "mặt dài", "mặt kim cương", "chọn gọng", "dáng mặt", "tôn dáng"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "Nguyên tắc cân bằng thị giác không gian: Chọn hình dáng gọng kính có hình học **tương phản** với đường nét tự nhiên của khuôn mặt:\n\n"
            "• **Mặt Tròn (Round Face):** Đường nét mềm mại, má bầu bĩnh → Nên chọn: **Gọng Vuông, Chữ Nhật, Đa Giác góc cạnh** để tạo cấu trúc góc cạnh, giúp khuôn mặt thanh thoát và thon gọn hơn. Tránh gọng tròn xoe.\n\n"
            "• **Mặt Vuông (Square Face):** Xương quai hàm góc cạnh, trán rộng → Nên chọn: **Gọng Tròn, Oval, Phi Công (Aviator)** có viền mảnh mềm mại để làm dịu các góc hàm vuông vức.\n\n"
            "• **Mặt Trái Xoan (Oval Face):** Tỷ lệ vàng nhân trắc học → Hợp với hầu như tất cả các kiểu dáng gọng (Vuông, Tròn, Mắt mèo, Nửa viền Browline).\n\n"
            "• **Mặt Dài (Oblong Face):** Chiều dài khuôn mặt lớn hơn bề ngang → Nên chọn: **Gọng Bản To, Vuông Oversize hoặc Browline** có cầu kính thấp để rút ngắn tỷ lệ chiều dọc khuôn mặt.\n\n"
            "• **Mặt Kim Cương / Tam Giác (Diamond Face):** Gò má cao, trán hẹp, cằm nhọn → Nên chọn: **Gọng Mắt Mèo (Cat-eye), Gọng Nửa Viền Clubmaster** để mở rộng phần trán và tôn nét gò má."
        )
    },

    # 8. KHOẢNG CÁCH ĐỒNG TỬ (PD) & QUANG SAI TÂM MẮT
    {
        "id": "kb_optical_pd_centering",
        "title": "Bác sĩ tư vấn: Khoảng Cách Đồng Tử (PD) & Tác hại của việc mài lệch tâm kính",
        "category": "Đo Khúc Xạ & Gia Công",
        "keywords": ["pd", "khoảng cách đồng tử", "tâm mắt", "mài lệch", "nhức mắt", "chóng mặt", "buồn nôn", "lăng kính"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "**1. Khoảng cách đồng tử (Pupillary Distance - PD) là gì?**\n"
            "Là khoảng cách đo bằng milimet (mm) giữa tâm của 2 con ngươi mắt khi nhìn thẳng vào vô cực. Chỉ số PD chuẩn của người Việt Nam dao động từ **60mm đến 66mm**.\n\n"
            "**2. Vì sao bắt buộc phải căn đúng PD khi cắt kính?**\n"
            "Mỗi tròng kính cận có một **Tâm Quang Học (Optical Center)** duy nhất - nơi ánh sáng đi qua mà không bị lệch góc. Kỹ thuật viên bắt buộc phải mài lắp sao cho tâm quang học của tròng kính trùng khớp $100\\%$ với tâm đồng tử mắt.\n\n"
            "**3. Tác hại khôn lường khi đeo kính lệch PD:**\n"
            "Tạo ra hiệu ứng lăng kính ngoài ý muốn (Prentice's Rule: $\\Delta = c \\times F$). Mắt bị ép phải liên tục gồng cơ điều tiết để hợp nhất 2 hình ảnh lệch nhau, dẫn đến: Đau nhức hốc mắt, đau đầu sau gáy, chóng mặt buồn nôn và dễ bị nhược thị hoặc tăng độ nhanh."
        )
    },

    # 9. CHẤT LIỆU GỌNG KÍNH Y KHOA: TITANIUM, ACETATE, TR90
    {
        "id": "kb_frame_materials_medical",
        "title": "Bác sĩ tư vấn: Phân tích Chất liệu Gọng Kính Y Khoa (Titanium, Acetate, TR90)",
        "category": "Gọng Kính & Nhân Trắc Học",
        "keywords": ["titanium", "titan", "acetate", "tr90", "dị ứng da", "nhẹ", "bền", "chất liệu", "mồ hôi muối"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "Lựa chọn chất liệu gọng kính không chỉ vì thẩm mỹ mà còn ảnh hưởng trực tiếp đến sức khỏe sống mũi và làn da:\n\n"
            "• **Titanium Y Tế (Titan nguyên chất & Beta-Titan):**\n"
            "  - Trọng lượng siêu nhẹ chỉ **7 - 12 gram**, giảm $70\\%$ áp lực tì đè lên sống mũi, không để lại vết hằn đỏ.\n  - Kháng ăn mòn tuyệt đối bởi mồ hôi muối, không bao giờ han gỉ hay ố xanh.\n  - $100\\%$ không gây kích ứng / dị ứng da (Hypoallergenic), thích hợp cho người có làn da nhạy cảm.\n\n"
            "• **Nhựa Cellulose Acetate cao cấp:**\n"
            "  - Chiết xuất từ sợi bông thực vật tự nhiên, an toàn thân thiện môi trường.\n  - Màu sắc sâu bóng sang trọng, có lõi kim loại bên trong càng kính cho phép uốn chỉnh ôm sát vành tai theo nhân trắc học từng người.\n\n"
            "• **Nhựa siêu dẻo TR90 / Ultem:**\n"
            "  - Đàn hồi cực cao, có thể uốn cong $180^\\circ$ mà không gãy gập, chống va đập tuyệt đối, an toàn cho trẻ em và người chơi thể thao."
        )
    },

    # 10. ĐỌC PHIẾU KHÁM MẮT Y KHOA (PRESCRIPTION DECODER)
    {
        "id": "kb_prescription_decoder_med",
        "title": "Bác sĩ tư vấn: Hướng dẫn giải mã ký hiệu trên Phiếu Khám Mắt Bệnh Viện",
        "category": "Đo Khúc Xạ & Gia Công",
        "keywords": ["phiếu khám", "đơn kính", "sph", "cyl", "axis", "od", "os", "add", "độ cận", "độ loạn"],
        "doctor_tone": "Chẩn đoán & Lời khuyên Bác sĩ Nhãn khoa",
        "content": (
            "Giải thích chuẩn y khoa các thuật ngữ trên phiếu đo khúc xạ mắt:\n\n"
            "• **OD (Oculus Dexter):** Mắt Phải | **OS (Oculus Sinister):** Mắt Trái | **OU (Oculus Uterque):** Cả Hai Mắt.\n"
            "• **SPH (Sphere - Độ Cầu):**\n"
            "  - Dấu **'-'** là Cận Thị (Ví dụ: -3.25D nghĩa là cận 3.25 độ).\n"
            "  - Dấu **'+'** là Viễn Thị (Ví dụ: +1.50D nghĩa là viễn 1.50 độ).\n"
            "• **CYL (Cylinder - Độ Loạn):** Độ trụ biểu thị mức độ loạn thị (Ví dụ: -1.00D).\n"
            "• **AXIS (Trục Loạn):** Hướng của kinh tuyến loạn thị ($1^\\circ$ đến $180^\\circ$). Luôn đi kèm với độ CYL.\n"
            "• **ADD (Addition - Độ Tăng Thêm):** Độ cộng thêm nhìn gần dành cho người lão thị (thường từ +1.00D đến +3.00D).\n"
            "• **PD (Pupillary Distance):** Khoảng cách đồng tử tâm mắt tính bằng milimet (mm)."
        )
    },

    # 11. DẤU HIỆU CẢNH BÁO BỆNH LÝ MẮT NGUY HIỂM CẦN ĐI VIỆN
    {
        "id": "kb_eye_emergency_warning",
        "title": "Bác sĩ cảnh báo: Các dấu hiệu bệnh lý mắt nguy hiểm cần đến Bệnh viện ngay",
        "category": "Bệnh Lý & Khúc Xạ",
        "keywords": ["đau nhức", "ruồi bay", "chớp sáng", "đỏ mắt", "mất thị lực", "cườm nước", "glaucoma", "bong võng mạc", "nguy hiểm"],
        "doctor_tone": "Cảnh báo Y Khoa Cấp Bách",
        "content": (
            "⚠️ **CẢNH BÁO Y KHOA: Nếu bạn gặp bất kỳ triệu chứng nào dưới đây, hãy đến ngay Bệnh viện Mắt chuyên khoa để cấp cứu kịp thời:**\n\n"
            "1. **Thấy chớp sáng liên tục hoặc đốm đen/ruồi bay dày đặc xuất hiện đột ngột:** Dấu hiệu rách hoặc bong võng mạc (Retinal Detachment), cần can thiệp laser trong vòng 24-48 giờ để tránh mù lòa vĩnh viễn.\n"
            "2. **Đau nhức mắt dữ dội lan lên nửa đầu kèm buồn nôn, nhìn đèn thấy quầng 7 màu:** Cơn tăng nhãn áp cấp (Acute Angle-Closure Glaucoma), áp lực nội nhãn tăng vọt có thể hủy hoại dây thần kinh thị giác chỉ sau vài giờ.\n"
            "3. **Mất thị lực đột ngột hoặc như có tấm rèm đen che khuất tầm nhìn:** Dấu hiệu tắc động mạch võng mạc trung tâm hoặc xuất huyết dịch kính.\n"
            "4. **Mắt đỏ tấy, chói cộm dữ dội và có đốm trắng đục trên tròng đen:** Dấu hiệu loét giác mạc do vi khuẩn hoặc nấm."
        )
    },

    # 12. CHÍNH SÁCH BẢO HÀNH & GIA CÔNG KÍNH MẮT KIM CHI
    {
        "id": "kb_kimchi_policies_guarantee",
        "title": "Chính sách Dịch vụ, Gia công chuẩn xác và Bảo hành trọn đời tại Kính Mắt Kim Chi",
        "category": "Chính Sách Cửa Hàng",
        "keywords": ["chính sách", "bảo hành", "đổi trả", "ưu đãi", "miễn phí", "cắt tròng", "kim chi", "vận chuyển", "hotline"],
        "doctor_tone": "Chính Sách & Cam Kết Dịch Vụ",
        "content": (
            "Kính Mắt Kim Chi (OptiStyle Pro) cam kết tiêu chuẩn kỹ thuật quang học chuẩn xác y khoa:\n\n"
            "1. **Gia công mài lắp tự động 3D:** Sử dụng máy mài kỹ thuật số Nidek Nhật Bản, căn chuẩn tâm đồng tử PD và trục loạn AXIS với sai số $\\le 0.01\\text{mm}$.\n"
            "2. **Bảo hiểm thị lực 30 ngày:** Miễn phí đổi mới tròng kính trong vòng 30 ngày nếu bạn cảm thấy mỏi mắt, chóng mặt hoặc chưa quen độ.\n"
            "3. **Bảo dưỡng trọn đời miễn phí:** Thay đệm ve mũi silicon, thay ốc vít titan, vệ sinh kính bằng sóng siêu âm và nắn chỉnh form kính định kỳ miễn phí.\n"
            "4. **Giao hàng toàn quốc:** Miễn phí vận chuyển cho đơn hàng từ 500.000đ, hỗ trợ mở hộp kiểm tra và thử kính tận nhà trước khi thanh toán (COD).\n"
            "5. **Hotline Bác sĩ & Kỹ thuật viên:** 1900 6868 | Mở cửa: 08:30 - 21:30 hàng ngày."
        )
    }
]


# ==============================================================================
# LỚP RAG ENGINE & BÁC SĨ QUANG HỌC AI THÔNG MINH
# ==============================================================================

class MedicalOptometryRAGEngine:
    def __init__(self):
        self.corpus = MEDICAL_OPTICAL_KNOWLEDGE_BASE
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
        words = [w.strip() for w in cleaned.split() if len(w.strip()) > 1]
        return words

    def _build_index(self):
        self.vocabulary = set()
        for doc in self.corpus:
            tokens = self._tokenize(doc["title"] + " " + doc["content"] + " " + " ".join(doc["keywords"]))
            self.vocabulary.update(tokens)

    def retrieve_relevant_medical_knowledge(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return self.corpus[:top_k]

        scored_docs = []
        for doc in self.corpus:
            doc_text = (doc["title"] + " " + doc["content"] + " " + " ".join(doc["keywords"])).lower()
            doc_tokens = self._tokenize(doc_text)
            
            # 1. Exact & Partial Term Match Score
            match_count = sum(1 for t in query_tokens if t in doc_tokens)
            
            # 2. Keyword Boost (Heavy Weight)
            keyword_matches = sum(3.5 for kw in doc["keywords"] if kw in query.lower())
            
            # 3. Title Relevance Boost
            title_matches = sum(4.0 for t in query_tokens if t in doc["title"].lower())
            
            score = match_count + keyword_matches + title_matches
            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored_docs[:top_k]]
        
        if not results:
            results = self.corpus[:top_k]
        return results

    def find_matching_products(self, query: str, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        matched_products = []
        if not db:
            return matched_products

        try:
            from app import crud
            frames = crud.get_frames(db, limit=30)
            lenses = crud.get_lenses(db)
            q_lower = query.lower()

            # 1. Match Frames by shape, material, gender
            for f in frames:
                f_score = 0
                if f.name.lower() in q_lower or f.shape.lower() in q_lower or f.material.lower() in q_lower:
                    f_score += 3
                if any(w in q_lower for w in ["gọng", "kính", "titan", "tròn", "vuông", "mắt mèo", "nam", "nữ", "dáng mặt"]):
                    if f.shape.lower() in q_lower or f.material.lower() in q_lower:
                        f_score += 1
                if f_score > 0:
                    matched_products.append({
                        "id": f.id,
                        "name": f.name,
                        "type": "frame",
                        "price": f.price,
                        "shape": f.shape,
                        "material": f.material,
                        "image_url": f.image_url,
                        "link": f"/products/{f.id}"
                    })

            # 2. Match Lenses by index or feature
            for l in lenses:
                l_score = 0
                if str(l.index_refraction) in q_lower or (l.name and any(kw in q_lower for kw in ["đổi màu", "blue cut", "chống ánh sáng xanh", "siêu mỏng", "chemi", "essilor"])):
                    l_score += 2
                if l_score > 0:
                    matched_products.append({
                        "id": l.id,
                        "name": l.name,
                        "type": "lens",
                        "price": l.price,
                        "brand": l.brand,
                        "index": l.index_refraction,
                        "link": "/cart"
                    })
        except Exception:
            pass

        return matched_products[:3]

    def generate_response(self, query: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        AI Doctor Synthesis Pipeline:
        1. Contextual Clinical Reasoning & Empathy
        2. Knowledge Retrieval & Extraction
        3. Medical Explanation + Practical Prescription Advice
        4. Optical Frame & Lens Matching from Store Inventory
        """
        q_lower = query.lower().strip()
        relevant_docs = self.retrieve_relevant_medical_knowledge(query, top_k=2)
        matched_products = self.find_matching_products(query, db)

        response_parts = []
        suggestions = []

        # Doctor Persona Salutation
        salutation = (
            "👨‍⚕️ **Bác sĩ Quang học AI (Kính Mắt Kim Chi) xin chào bạn!**\n\n"
            "Dựa trên tình trạng thị lực và câu hỏi của bạn, tôi xin đưa ra lời khuyên chuyên môn y khoa như sau:\n\n"
        )
        response_parts.append(salutation)

        # CLINICAL SCENARIO 1: Myopia / Increasing diopters / School myopia
        if any(w in q_lower for w in ["cận thị", "tăng độ", "nhìn xa mờ", "cận nặng", "độ cận", "nheo mắt"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_myopia_care"), relevant_docs[0])
            response_parts.append(f"### 🔬 **Chẩn Đoán & Tư Vấn Cận Thị Chuyên Sâu**\n\n{doc['content']}")
            suggestions = [
                "Cận -4.50D nên chọn tròng chiết suất nào?",
                "Tròng chống ánh sáng xanh Blue Cut loại nào tốt?",
                "Làm sao để mắt không bị tăng độ khi dùng máy tính?"
            ]

        # CLINICAL SCENARIO 2: Astigmatism & AXIS
        elif any(w in q_lower for w in ["loạn thị", "loạn", "bóng mờ", "trục", "axis", "cyl", "song thị"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_astigmatism_care"), relevant_docs[0])
            response_parts.append(f"### 🎯 **Chẩn Đoán Tật Loạn Thị & Căn Chỉnh Trục Loạn AXIS**\n\n{doc['content']}")
            suggestions = [
                "Vừa cận vừa loạn thì cắt kính thế nào?",
                "Cách đọc phiếu khám mắt có độ loạn",
                "Đo khoảng cách đồng tử PD tự động 📸"
            ]

        # CLINICAL SCENARIO 3: Computer Vision Syndrome / Eye Strain / Dry eyes
        elif any(w in q_lower for w in ["mỏi mắt", "khô mắt", "máy tính", "điện thoại", "cvs", "nhức mắt", "rát mắt", "ánh sáng xanh"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_digital_eye_strain_cvs"), relevant_docs[0])
            response_parts.append(f"### 💻 **Phác Đồ Chăm Sóc Mắt Mỏi & Khô Mắt Văn Phòng**\n\n{doc['content']}")
            suggestions = [
                "Tròng kính Blue Cut và Blue Control khác nhau gì?",
                "Quy tắc 20-20-20 bảo vệ mắt là gì?",
                "Gọng kính Titanium siêu nhẹ chống mỏi sống mũi"
            ]

        # CLINICAL SCENARIO 4: Presbyopia / Aging eyes / Progressives
        elif any(w in q_lower for w in ["lão thị", "người lớn tuổi", "đọc sách", "đa tròng", "hai tròng", "tuổi 40", "add"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_presbyopia_progressives"), relevant_docs[0])
            response_parts.append(f"### 👓 **Giải Pháp Lão Thị & Kính Đa Tròng Không Đường Biên**\n\n{doc['content']}")
            suggestions = [
                "Kính đa tròng có khó đeo không?",
                "Độ ADD trên đơn kính là gì?",
                "Gọng kính Titanium cao cấp cho người lớn tuổi"
            ]

        # CLINICAL SCENARIO 5: Refractive Index selection (1.56, 1.60, 1.67, 1.74)
        elif any(w in q_lower for w in ["chiết suất", "1.56", "1.60", "1.67", "1.74", "dày", "mỏng", "trọng lượng"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_lens_index_matrix"), relevant_docs[0])
            response_parts.append(f"### 💎 **Hướng Dẫn Chọn Chiết Suất Tròng Kính Y Khoa**\n\n{doc['content']}")
            suggestions = [
                "Cận -6.00D nên dùng chiết suất 1.67 hay 1.74?",
                "Tròng kính đổi màu khi ra nắng giá bao nhiêu?",
                "Gọng kính nửa viền xẻ cước dùng tròng nào?"
            ]

        # CLINICAL SCENARIO 6: Photochromic / Transitions
        elif any(w in q_lower for w in ["đổi màu", "transitions", "ra nắng", "râm cận", "chống chói"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_transitions_photochromic"), relevant_docs[0])
            response_parts.append(f"### ☀️ **Tròng Kính Cận Đổi Màu Thông Minh (Transitions)**\n\n{doc['content']}")
            suggestions = [
                "Tròng đổi màu Xám Khói hay Nâu Trà tốt hơn?",
                "Gọng kính Phi công (Aviator) thời trang",
                "Cách đặt cắt tròng online kèm số độ"
            ]

        # CLINICAL SCENARIO 7: Face Shape Consultation
        elif any(w in q_lower for w in ["mặt tròn", "mặt vuông", "mặt trái xoan", "mặt dài", "mặt kim cương", "dáng mặt", "chọn gọng"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_face_shape_anatomy"), relevant_docs[0])
            response_parts.append(f"### 📐 **Nhân Trắc Học: Chọn Dáng Gọng Tôn Nét Khuôn Mặt**\n\n{doc['content']}")
            suggestions = [
                "Thử Kính AR Trực Tiếp Trên Khuôn Mặt Thật 📸",
                "Gọng kính Vuông cho mặt tròn",
                "Gọng kính Tròn cho mặt vuông"
            ]

        # CLINICAL SCENARIO 8: Optical PD & Centering
        elif any(w in q_lower for w in ["pd", "khoảng cách đồng tử", "tâm mắt", "mài lệch"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_optical_pd_centering"), relevant_docs[0])
            response_parts.append(f"### 📏 **Khoảng Cách Đồng Tử (PD) & Chuẩn Tâm Quang Học**\n\n{doc['content']}")
            suggestions = [
                "Tự đo khoảng cách đồng tử PD bằng Camera AI",
                "Đeo kính lệch độ có bị nhược thị không?",
                "Quy trình cắt kính online tại Kim Chi"
            ]

        # CLINICAL SCENARIO 9: Prescription Decoder (Đọc đơn kính)
        elif any(w in q_lower for w in ["phiếu khám", "đơn kính", "sph", "cyl", "axis", "od", "os", "add"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_prescription_decoder_med"), relevant_docs[0])
            response_parts.append(f"### 📋 **Giải Mã Chi Tiết Ký Hiệu Trên Phiếu Khám Mắt**\n\n{doc['content']}")
            suggestions = [
                "Tải ảnh đơn kính lên giỏ hàng để thợ mài tròng",
                "Chiết suất 1.67 siêu mỏng",
                "Gọng kính Titan nguyên chất"
            ]

        # CLINICAL SCENARIO 10: Eye Emergency Warnings
        elif any(w in q_lower for w in ["đau nhức", "ruồi bay", "chớp sáng", "đỏ mắt", "cấp cứu", "bong võng mạc", "mất thị lực"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_eye_emergency_warning"), relevant_docs[0])
            response_parts.append(f"### 🚨 **Cảnh Báo Y Khoa: Dấu Hiệu Bệnh Mắt Cần Cấp Cứu**\n\n{doc['content']}")
            suggestions = [
                "Địa chỉ các bệnh viện mắt uy tín",
                "Cách sơ cứu khi bị dị vật vào mắt",
                "Nước mắt nhân tạo không chất bảo quản"
            ]

        # CLINICAL SCENARIO 11: Store policies & Warranty
        elif any(w in q_lower for w in ["bảo hành", "đổi trả", "ship", "cửa hàng", "kim chi", "địa chỉ", "hotline", "ưu đãi"]):
            doc = next((d for d in relevant_docs if d["id"] == "kb_kimchi_policies_guarantee"), relevant_docs[0])
            response_parts.append(f"### 🛡️ **Chính Sách & Cam Kết Kỹ Thuật Quang Học Kim Chi**\n\n{doc['content']}")
            suggestions = [
                "Xem bộ sưu tập gọng Titan siêu nhẹ",
                "Phòng Thử Kính Ảo AR 📸",
                "Bảng giá các loại tròng kính chính hãng"
            ]

        # DEFAULT CLINICAL ADVICE
        else:
            primary_doc = relevant_docs[0] if relevant_docs else self.corpus[0]
            response_parts.append(
                f"Cảm ơn bạn đã chia sẻ thắc mắc về *'{query}'*.\n\n"
                f"📌 **{primary_doc['title']}**:\n\n{primary_doc['content']}\n\n"
                f"💡 *Lời khuyên từ Bác sĩ: Để đôi mắt luôn sáng khỏe và thị lực đạt $10/10$, bạn nên khám mắt định kỳ 6 tháng/lần và đeo kính có lớp phủ chống tia UV/ánh sáng xanh khi làm việc.*"
            )
            suggestions = [
                "Tư vấn chọn tròng theo độ cận",
                "Gọng kính phù hợp với dáng mặt",
                "Tròng chống ánh sáng xanh Blue Cut",
                "Thử Kính AR Ảo Trên Mặt Thật 📸"
            ]

        # Attach Matching Medical Product Recommendations
        if matched_products:
            prod_text = "\n\n---\n#### 🩺 **Gợi ý Kính & Tròng Kính Y Khoa Phù Hợp Cho Bạn:**\n"
            for p in matched_products:
                if p["type"] == "frame":
                    price_fmt = f"{p['price']:,.0f}đ"
                    prod_text += f"• **[{p['name']}]({p['link']})** - Dáng {p['shape']} ({p['material']}) - Giá: **{price_fmt}**\n"
                else:
                    price_fmt = f"{p['price']:,.0f}đ"
                    prod_text += f"• **{p['name']}** - Chiết suất {p['index']} ({p.get('brand', 'Chính hãng')}) - Giá: **{price_fmt}**\n"
            response_parts.append(prod_text)

        full_reply = "\n".join(response_parts)
        sources = [d["title"] for d in relevant_docs]

        return {
            "reply": full_reply,
            "suggestions": suggestions,
            "recommended_products": matched_products,
            "sources": sources
        }


# Global Singleton Medical RAG Engine Instance
rag_engine = MedicalOptometryRAGEngine()
