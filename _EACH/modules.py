import json
from SDS.SDS_PAGE import getExampleSDS_PAGE,virtualSDSPage_2DGaussian,parseFasta
from _EACH.protein import Protein
from utils.helperFunctions import extractSetting

def select(moduleIdentifier,selectedSettings,moduleData):
    """
    Dispatch the requested module to its backend implementation and return the simulated SDS-PAGE image.

    Settings (see module JSON):
    - Varies per module; each module function documents its own settings.

    :param moduleIdentifier: String module id (e.g., "fasta_input") coming from the frontend JSON definition.
    :param selectedSettings: Dict of user-selected values for the active module.
    :param moduleData: Loaded JSON defining all modules and their settings (options, defaults, etc.).
    :return: SDS-PAGE plot generated from the proteins produced by the module.
    """
    match moduleIdentifier:
        case "fasta_input":
            proteins = fasta_input(moduleIdentifier, selectedSettings, moduleData)
            return virtualSDSPage_2DGaussian(proteins)
        case "size_exclusion":
            proteins = size_exclusion(moduleIdentifier, selectedSettings, moduleData)
            return virtualSDSPage_2DGaussian(proteins)

        case _: # Add new modules above 
            # Do not add modules below
            raise NotImplementedError(f"Module: {moduleIdentifier} is not implemented yet.")
        

def fasta_input(moduleIdentifier, selectedSettings,moduleData):
    """
    Load proteins from a selected FASTA file and convert sequences into Protein objects.

    Settings (fasta_input.json):
    - "Select FASTA file" (ChoiceField): maps a human-readable name to a FASTA filepath.

    :param selectedSettings: Dict containing the chosen FASTA file key from the UI.
    :param moduleData: Module definitions used to map the chosen key to an actual FASTA path.
    :return: List of Protein instances created from the FASTA sequences.

    """
    # Resolve selected label to actual FASTA path
    filePath = extractSetting("Select FASTA file",moduleIdentifier,selectedSettings,moduleData)
    sequences = parseFasta(filePath)
    Protein.deleteAllProteins()
    proteinList = []
    for header, sequence in sequences.items():
        proteinList.append(Protein(header, sequence))
    return proteinList

def size_exclusion(moduleIdentifier, selectedSettings, moduleData):
    sec_mode = extractSetting("SEC mode", moduleIdentifier, selectedSettings, moduleData)
    keepInsideOutside = "inside"

    def _get_abundance(p):
        if hasattr(p, "get_abundance") and callable(p.get_abundance):
            return float(p.get_abundance() or 0.0)
        return float(getattr(p, "abundance", 0.0) or 0.0)

    def _get_weight_kda(p):
        # prefer attribute used elsewhere in your codebase
        w = getattr(p, "weight", None)
        if w is not None:
            return float(w)
        # fallback if getter exists
        if hasattr(p, "get_weight") and callable(p.get_weight):
            gw = p.get_weight()
            if gw is not None:
                return float(gw)
        return None

    def _apply_window(min_kda, max_kda, label=None):
        min_kda = float(min_kda)
        max_kda = float(max_kda)
        if min_kda > max_kda:
            min_kda, max_kda = max_kda, min_kda
        min_kda = max(min_kda, 0.0)
        max_kda = max(max_kda, 0.0)

        Protein.fractionateProteinsByMolecularWeight(
            keepInsideOutsideSelection=keepInsideOutside,
            minWeight=min_kda,
            maxWeight=max_kda,
        )

        if label:
            for p in Protein.getAllProteins():
                p.modifications.append(f"SEC: {label}")

    # ---------------- simulate ----------------
    if sec_mode == "simulate":
        col_range = extractSetting("SEC column", moduleIdentifier, selectedSettings, moduleData)
        if not isinstance(col_range, (list, tuple)) or len(col_range) != 2:
            raise ValueError("SEC column must resolve to [min_kDa, max_kDa].")

        chosen_label = selectedSettings.get("SEC column", None)
        _apply_window(col_range[0], col_range[1], label=chosen_label)
        return Protein.getAllProteins()

    # ---------------- recommend ----------------
    if sec_mode == "recommend":
        user_min = float(extractSetting("Target minimum MW (kDa)", moduleIdentifier, selectedSettings, moduleData))
        user_max = float(extractSetting("Target maximum MW (kDa)", moduleIdentifier, selectedSettings, moduleData))
        if user_min > user_max:
            user_min, user_max = user_max, user_min

        options = moduleData[moduleIdentifier]["settings"]["SEC column"]["options"]  # label -> [min,max]
        proteins = Protein.getAllProteins()

        def abundance_in_window(a, b):
            a = float(a); b = float(b)
            if a > b:
                a, b = b, a
            total = 0.0
            for p in proteins:
                ab = _get_abundance(p)
                if ab <= 0.0:
                    continue
                w = _get_weight_kda(p)
                if w is None:
                    continue
                if a <= w <= b:
                    total += ab
            return total

        best_label = None
        best_eff_min = None
        best_eff_max = None
        best_score = -1.0

        for label, rng in options.items():
            col_min, col_max = float(rng[0]), float(rng[1])
            if col_min > col_max:
                col_min, col_max = col_max, col_min

            eff_min = max(col_min, user_min)
            eff_max = min(col_max, user_max)
            if eff_min > eff_max:
                continue

            in_target = abundance_in_window(eff_min, eff_max)
            in_column = abundance_in_window(col_min, col_max)
            if in_column <= 0.0:
                continue

            score = in_target / in_column  # purity
            if score > best_score:
                best_score = score
                best_label = label
                best_eff_min, best_eff_max = eff_min, eff_max

        # If nothing matches, leave proteins unchanged
        if best_label is None:
            for p in Protein.getAllProteins():
                p.modifications.append("SEC: no suitable column found for target window")
            return Protein.getAllProteins()
        selectedSettings["SEC column"] = best_label

        _apply_window(best_eff_min, best_eff_max, label=best_label)
        return Protein.getAllProteins()

    raise ValueError(f"Invalid SEC mode: {sec_mode}")

