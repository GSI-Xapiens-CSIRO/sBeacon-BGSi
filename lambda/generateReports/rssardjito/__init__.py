from .md.en_md_neg import generate as en_md_neg_generate
from .md.en_md_pos import generate as en_md_pos_generate
from .md.id_md_neg import generate as id_md_neg_generate
from .md.id_md_pos import generate as id_md_pos_generate

from .crd.en_crd_neg import generate as en_crd_neg_generate
from .crd.en_crd_pos import generate as en_crd_pos_generate
from .crd.id_crd_neg import generate as id_crd_neg_generate
from .crd.id_crd_pos import generate as id_crd_pos_generate

from .generic.en_gen_neg import generate as en_gen_neg_generate
from .generic.en_gen_pos import generate as en_gen_pos_generate
from .generic.id_gen_neg import generate as id_gen_neg_generate
from .generic.id_gen_pos import generate as id_gen_pos_generate


def get_report_generator(kind, mode, language):
    """
    Get the appropriate report generator function based on lab, kind, and language.
    """
    if kind == "neg":
        if mode == "generic":
            if language == "en":
                return en_gen_neg_generate
            elif language == "id":
                return id_gen_neg_generate
        elif mode == "crd":
            if language == "en":
                return en_crd_neg_generate
            elif language == "id":
                return id_crd_neg_generate
        elif mode == "md":
            if language == "en":
                return en_md_neg_generate
            elif language == "id":
                return id_md_neg_generate
        else:
            raise ValueError("Invalid mode or not implemented")
    elif kind == "pos":
        if mode == "generic":
            if language == "en":
                return en_gen_pos_generate
            elif language == "id":
                return id_gen_pos_generate
        elif mode == "crd":
            if language == "en":
                return en_crd_pos_generate
            elif language == "id":
                return id_crd_pos_generate
        elif mode == "md":
            if language == "en":
                return en_md_pos_generate
            elif language == "id":
                return id_md_pos_generate
        else:
            raise ValueError("Invalid mode or not implemented")
    else:
        raise ValueError("Invalid kind or not implemented")
