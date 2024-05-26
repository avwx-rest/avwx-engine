"""Cleaners for cloud elements."""

from avwx.static.core import CLOUD_LIST


def separate_cloud_layers(text: str) -> str:
    """Check for missing spaces in front of cloud layers.
    Ex: TSFEW004SCT012FEW///CBBKN080
    """
    for cloud in CLOUD_LIST:
        if cloud in text and f" {cloud}" not in text:
            start, counter = 0, 0
            while text.count(cloud) != text.count(f" {cloud}"):
                cloud_index = start + text[start:].find(cloud)
                if len(text[cloud_index:]) >= 3:
                    target = text[cloud_index + len(cloud) : cloud_index + len(cloud) + 3]
                    if target.isdigit() or not target.strip("/"):
                        text = f"{text[:cloud_index]} {text[cloud_index:]}"
                start = cloud_index + len(cloud) + 1
                # Prevent infinite loops
                if counter > text.count(cloud):
                    break
                counter += 1
    return text
