#!/usr/bin/env python3
"""
Benchmark script for Al-Furqan embedding models.

Measures:
    - Time per text embedding
    - Total throughput
    - Memory usage
    - Embedding dimension and quality checks

Usage:
    python scripts/benchmark_embeddings.py
"""

import gc
import logging
import os
import sys
import time
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import numpy as np  # pylint: disable=wrong-import-position

from al_furqan import setup_logging  # pylint: disable=wrong-import-position

logger = logging.getLogger(__name__)

# Sample Islamic texts for benchmarking (100+ texts)
SAMPLE_TEXTS = [
    # Quran verses (Arabic)
    "بسم الله الرحمن الرحيم",
    "الحمد لله رب العالمين",
    "الرحمن الرحيم",
    "مالك يوم الدين",
    "إياك نعبد وإياك نستعين",
    "اهدنا الصراط المستقيم",
    "صراط الذين أنعمت عليهم غير المغضوب عليهم ولا الضالين",
    "ألم ذلك الكتاب لا ريب فيه هدى للمتقين",
    "الذين يؤمنون بالغيب ويقيمون الصلاة ومما رزقناهم ينفقون",
    "والذين يؤمنون بما أنزل إليك وما أنزل من قبلك وبالآخرة هم يوقنون",
    "أولئك على هدى من ربهم وأولئك هم المفلحون",
    "إن الذين كفروا سواء عليهم أأنذرتهم أم لم تنذرهم لا يؤمنون",
    "ختم الله على قلوبهم وعلى سمعهم وعلى أبصارهم غشاوة ولهم عذاب عظيم",
    "ومن الناس من يقول آمنا بالله وباليوم الآخر وما هم بمؤمنين",
    "يخادعون الله والذين آمنوا وما يخدعون إلا أنفسهم وما يشعرون",
    "في قلوبهم مرض فزادهم الله مرضا ولهم عذاب أليم بما كانوا يكذبون",
    "وإذا قيل لهم لا تفسدوا في الأرض قالوا إنما نحن مصلحون",
    "ألا إنهم هم المفسدون ولكن لا يشعرون",
    "يا أيها الناس اعبدوا ربكم الذي خلقكم والذين من قبلكم لعلكم تتقون",
    "الله لا إله إلا هو الحي القيوم لا تأخذه سنة ولا نوم",
    "له ما في السماوات وما في الأرض من ذا الذي يشفع عنده إلا بإذنه",
    "يعلم ما بين أيديهم وما خلفهم ولا يحيطون بشيء من علمه إلا بما شاء",
    "وسع كرسيه السماوات والأرض ولا يؤوده حفظهما وهو العلي العظيم",
    "لا إكراه في الدين قد تبين الرشد من الغي",
    "آمن الرسول بما أنزل إليه من ربه والمؤمنون",
    # Hadith texts
    "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
    "من حسن إسلام المرء تركه ما لا يعنيه",
    "لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه",
    "المسلم من سلم المسلمون من لسانه ويده",
    "من كان يؤمن بالله واليوم الآخر فليقل خيرا أو ليصمت",
    "لا ضرر ولا ضرار",
    "الدين النصيحة",
    "إن الله طيب لا يقبل إلا طيبا",
    "اتق الله حيثما كنت وأتبع السيئة الحسنة تمحها وخالق الناس بخلق حسن",
    "ازهد في الدنيا يحبك الله وازهد فيما عند الناس يحبك الناس",
    "الطهور شطر الإيمان والحمد لله تملأ الميزان",
    "سبحان الله والحمد لله تملآن ما بين السماوات والأرض",
    "والصلاة نور والصدقة برهان والصبر ضياء",
    "والقرآن حجة لك أو عليك",
    "كل الناس يغدو فبائع نفسه فمعتقها أو موبقها",
    "إن الله لا ينظر إلى صوركم وأموالكم ولكن ينظر إلى قلوبكم وأعمالكم",
    "المؤمن القوي خير وأحب إلى الله من المؤمن الضعيف وفي كل خير",
    "احرص على ما ينفعك واستعن بالله ولا تعجز",
    "لو أنكم تتوكلون على الله حق توكله لرزقكم كما يرزق الطير",
    "تغدو خماصا وتروح بطانا",
    # Fiqh principles
    "الأمور بمقاصدها",
    "اليقين لا يزول بالشك",
    "المشقة تجلب التيسير",
    "الضرر يزال",
    "العادة محكمة",
    "درء المفاسد أولى من جلب المصالح",
    "الضرورات تبيح المحظورات",
    "ما أبيح للضرورة يقدر بقدرها",
    "الأصل في الأشياء الإباحة",
    "الأصل براءة الذمة",
    # More Quran
    "قل هو الله أحد الله الصمد لم يلد ولم يولد ولم يكن له كفوا أحد",
    "قل أعوذ برب الفلق من شر ما خلق",
    "ومن شر غاسق إذا وقب ومن شر النفاثات في العقد",
    "ومن شر حاسد إذا حسد",
    "قل أعوذ برب الناس ملك الناس إله الناس",
    "من شر الوسواس الخناس الذي يوسوس في صدور الناس من الجنة والناس",
    "إنا أعطيناك الكوثر فصل لربك وانحر إن شانئك هو الأبتر",
    "إنا أنزلناه في ليلة القدر وما أدراك ما ليلة القدر",
    "ليلة القدر خير من ألف شهر تنزل الملائكة والروح فيها بإذن ربهم من كل أمر",
    "سلام هي حتى مطلع الفجر",
    "والعصر إن الإنسان لفي خسر",
    "إلا الذين آمنوا وعملوا الصالحات وتواصوا بالحق وتواصوا بالصبر",
    "ألهاكم التكاثر حتى زرتم المقابر",
    "كلا سوف تعلمون ثم كلا سوف تعلمون",
    "والضحى والليل إذا سجى ما ودعك ربك وما قلى",
    "وللآخرة خير لك من الأولى ولسوف يعطيك ربك فترضى",
    "ألم نشرح لك صدرك ووضعنا عنك وزرك الذي أنقض ظهرك",
    "ورفعنا لك ذكرك فإن مع العسر يسرا إن مع العسر يسرا",
    # More Hadith
    "الدنيا سجن المؤمن وجنة الكافر",
    "ما ملأ ابن آدم وعاء شرا من بطنه",
    "بحسب ابن آدم لقيمات يقمن صلبه",
    "فإن كان لا محالة فاعلا فثلث لطعامه وثلث لشرابه وثلث لنفسه",
    "خيركم من تعلم القرآن وعلمه",
    "من سلك طريقا يلتمس فيه علما سهل الله له به طريقا إلى الجنة",
    "إن الملائكة لتضع أجنحتها لطالب العلم رضا بما يصنع",
    "فضل العالم على العابد كفضل القمر ليلة البدر على سائر الكواكب",
    "إن العلماء ورثة الأنبياء وإن الأنبياء لم يورثوا دينارا ولا درهما",
    "وإنما ورثوا العلم فمن أخذه أخذ بحظ وافر",
    "طلب العلم فريضة على كل مسلم",
    "الراحمون يرحمهم الرحمن ارحموا من في الأرض يرحمكم من في السماء",
    "من لا يرحم لا يرحم",
    "ليس منا من لم يرحم صغيرنا ويعرف حق كبيرنا",
    "الساعي على الأرملة والمسكين كالمجاهد في سبيل الله",
    "ما نقصت صدقة من مال وما زاد الله عبدا بعفو إلا عزا",
    "وما تواضع أحد لله إلا رفعه الله",
    "إن الله جميل يحب الجمال",
    "إن الله رفيق يحب الرفق في الأمر كله",
    "إن الرفق لا يكون في شيء إلا زانه ولا ينزع من شيء إلا شانه",
    "أكمل المؤمنين إيمانا أحسنهم خلقا",
    "وخياركم خياركم لنسائهم",
    "استوصوا بالنساء خيرا",
    "خير الناس أنفعهم للناس",
    "المؤمن للمؤمن كالبنيان يشد بعضه بعضا",
    "مثل المؤمنين في توادهم وتراحمهم وتعاطفهم مثل الجسد الواحد",
    "إذا اشتكى منه عضو تداعى له سائر الجسد بالسهر والحمى",
    "لا تحاسدوا ولا تناجشوا ولا تباغضوا ولا تدابروا",
    "ولا يبع بعضكم على بيع بعض وكونوا عباد الله إخوانا",
    "المسلم أخو المسلم لا يظلمه ولا يخذله ولا يحقره",
    "بحسب امرئ من الشر أن يحقر أخاه المسلم",
    "كل المسلم على المسلم حرام دمه وماله وعرضه",
]

assert len(SAMPLE_TEXTS) >= 100, f"Need 100+ sample texts, have {len(SAMPLE_TEXTS)}"


def get_memory_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        import resource  # pylint: disable=import-outside-toplevel
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024  # Convert KB to MB on Linux
    except ImportError:
        return 0.0


def benchmark_model(model_key: str) -> Optional[dict]:  # pylint: disable=too-many-locals
    """Benchmark a single embedding model."""
    from al_furqan.kb.embeddings import EmbeddingModel  # pylint: disable=import-outside-toplevel

    logger.info("%s", "=" * 60)
    logger.info("Benchmarking: %s", model_key)
    logger.info("%s", "=" * 60)

    gc.collect()
    mem_before = get_memory_mb()

    try:
        t0 = time.time()
        model = EmbeddingModel(model_key)
        load_time = time.time() - t0
        logger.info("  Model loaded in %.2fs", load_time)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("  Failed to load: %s", e)
        return None

    mem_after_load = get_memory_mb()

    # Benchmark batch embedding
    t0 = time.time()
    embeddings = model.embed(SAMPLE_TEXTS)
    batch_time = time.time() - t0

    mem_after_embed = get_memory_mb()

    # Benchmark individual embeddings
    t0 = time.time()
    for text in SAMPLE_TEXTS[:20]:
        model.embed_query(text)
    individual_time = time.time() - t0

    # Validate embeddings
    emb_array = np.array(embeddings)
    norms = np.linalg.norm(emb_array, axis=1)
    mean_norm = float(np.mean(norms))

    # Similarity sanity check
    sim_related = model.similarity(
        "الصلاة عماد الدين",
        "أقيموا الصلاة وآتوا الزكاة",
    )
    sim_unrelated = model.similarity(
        "الصلاة عماد الدين",
        "الطبخ فن جميل",
    )

    results = {
        "model": model_key,
        "model_path": model.model_path,
        "dimension": model.dimension,
        "num_texts": len(SAMPLE_TEXTS),
        "load_time_s": round(load_time, 3),
        "batch_time_s": round(batch_time, 3),
        "time_per_text_ms": round(batch_time / len(SAMPLE_TEXTS) * 1000, 2),
        "individual_20_time_s": round(individual_time, 3),
        "mem_model_mb": round(mem_after_load - mem_before, 1),
        "mem_total_mb": round(mem_after_embed, 1),
        "mean_l2_norm": round(mean_norm, 6),
        "sim_related": round(sim_related, 4),
        "sim_unrelated": round(sim_unrelated, 4),
        "sim_delta": round(sim_related - sim_unrelated, 4),
    }

    return results


def print_results_table(all_results: list[dict]) -> None:
    """Print benchmark results as a formatted table."""
    if not all_results:
        logger.info("No results to display.")
        return

    logger.info("%s", "=" * 80)
    logger.info("BENCHMARK RESULTS SUMMARY")
    logger.info("%s", "=" * 80)

    headers = [
        ("Model", "model"),
        ("Dim", "dimension"),
        ("Load(s)", "load_time_s"),
        ("Batch(s)", "batch_time_s"),
        ("ms/text", "time_per_text_ms"),
        ("Mem(MB)", "mem_total_mb"),
        ("L2 Norm", "mean_l2_norm"),
        ("Sim(rel)", "sim_related"),
        ("Sim(unrel)", "sim_unrelated"),
        ("d Sim", "sim_delta"),
    ]

    # Print header
    header_line = " | ".join(f"{h[0]:>10}" for h in headers)
    logger.info("%s", header_line)
    logger.info("%s", "-" * len(header_line))

    # Print rows
    for r in all_results:
        row = " | ".join(f"{str(r.get(h[1], 'N/A')):>10}" for h in headers)
        logger.info("%s", row)

    logger.info("Texts embedded: %d", all_results[0]["num_texts"])


def main() -> None:
    """Execute main."""
    setup_logging()
    logger.info("Al-Furqan Embedding Benchmark")
    logger.info("Sample texts: %d", len(SAMPLE_TEXTS))

    all_results = []

    for model_key in ["minilm", "camelbert"]:
        result = benchmark_model(model_key)
        if result:
            all_results.append(result)

    print_results_table(all_results)


if __name__ == "__main__":
    main()
