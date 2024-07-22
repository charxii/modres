from typing import Dict, List, Union
import re
import html


class ResumeSection:
    def __init__(self, title: str):
        self.title: str = title
        self.content: List[Union[Dict, List]] = []
        self.enabled: bool = True


class Resume:
    def __init__(self, resume_path: str):
        self.personal_info: List[str] = []
        self.sections: List[ResumeSection] = []
        self.resume_path: str = resume_path
        self._parse_resume()

    def _parse_resume(self) -> None:
        with open(self.resume_path, "r") as file:
            content = file.read()

        lines = content.split("\n")
        current_section: ResumeSection = None
        parsing_personal_info = True
        current_entry = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("#"):
                parsing_personal_info = False
                if current_section:
                    self._append_entry(current_entry, current_section)
                current_entry = {"type": "entry", "enabled": True}
                current_section = ResumeSection(title=line[1:].strip())
                self.sections.append(current_section)
            elif parsing_personal_info:
                self.personal_info.append(line)
            elif line.startswith("/list"):
                self._parse_list_item(line, current_section)
            elif current_section:
                self._parse_entry_item(line, current_entry, current_section)

        if current_entry:
            current_section.content.append(current_entry)

    def _append_entry(self, entry: Dict, section: ResumeSection) -> None:
        if len(entry) == 2 and "type" in entry and "enabled" in entry:
            return  # Don't add empty entries
        section.content.append(entry)

    def _parse_list_item(self, line: str, current_section: ResumeSection) -> None:
        match = re.match(r"/list \((.+?)\)\((.+?)\)", line)
        if match and current_section:
            group, items = match.groups()
            current_section.content.append(
                {
                    "type": "list",
                    "group": group,
                    "items": [
                        {"text": item.strip(), "enabled": True}
                        for item in items.split(",")
                    ],
                    "enabled": True,
                }
            )

    def _parse_entry_item(
        self, line: str, current_entry: Dict, current_section: ResumeSection
    ) -> None:
        entry_fields = ["company", "date", "title", "location"]

        if line.startswith("-"):
            if "bullet_points" not in current_entry:
                current_entry["bullet_points"] = []
            current_entry["bullet_points"].append(line[1:].strip())
        else:
            filled_fields = sum(1 for field in entry_fields if field in current_entry)
            if line == "/none":
                line = ""
            if filled_fields < len(entry_fields):
                current_entry[entry_fields[filled_fields]] = line
            else:
                self._append_entry(current_entry.copy(), current_section)
                current_entry.clear()
                current_entry.update(
                    {"type": "entry", "enabled": True, entry_fields[0]: line}
                )

    def to_text(self) -> str:
        output = self._format_personal_info()
        for section in self.sections:
            if not section.enabled:
                continue
            output += self._format_section(section)
        return output.strip("\n")

    def _format_personal_info(self) -> str:
        return "\n".join(self.personal_info) + "\n\n"

    def _format_section(self, section: ResumeSection) -> str:
        output = f"{section.title}\n\n"
        for item in section.content:
            if not item["enabled"]:
                continue
            if item["type"] == "entry":
                output += self._format_entry(item)
            elif item["type"] == "list":
                output += self._format_list(item)

        # this looks stupid but its because
        # we need entries to have spacing, but not lists
        # so to fix the end, we make sure there are only
        # two newlines in the end
        return output.strip("\n") + "\n\n"

    def _format_entry(self, entry: Dict) -> str:
        output = ""
        for k, v in entry.items():
            if k == "bullet_points":
                output += "\n".join(f"- {i}" for i in v) + "\n"
            elif k not in ["type", "enabled"]:
                output += f"{v}\n"
        return output + "\n"

    def _format_list(self, list_item: Dict) -> str:
        enabled_items = [i["text"] for i in list_item["items"] if i["enabled"]]
        if enabled_items:
            return f"{list_item['group']}: {', '.join(enabled_items)}\n"
        return ""

    def to_dict(self) -> Dict:
        return {
            "personal_info": self.personal_info,
            "sections": [
                {
                    "title": section.title,
                    "enabled": section.enabled,
                    "content": section.content,
                }
                for section in self.sections
            ],
        }

    def to_html(self) -> str:
        html_content = f"<div class='resume-container'>{self._personal_info_to_html()}"

        for section in self.sections:
            if section.enabled:
                html_content += f"<div class='section'><h2>{html.escape(section.title.upper())}</h2>"
                for item in section.content:
                    if item["enabled"]:
                        if item["type"] == "entry":
                            html_content += self._entry_to_html(item)
                        elif item["type"] == "list":
                            html_content += self._list_to_html(item)
                html_content += "</div>"

        html_content += "</div>"
        return html_content

    def _personal_info_to_html(self) -> str:
        if not self.personal_info:
            return ""

        name = self.personal_info[0]
        other_info = self.personal_info[1:]

        html_content = (
            f"<div class='personal-info'><h1 class='name'>{html.escape(name)}</h1>"
        )
        if other_info:
            html_content += (
                "<div class='other-info'>"
                + " | ".join(html.escape(line) for line in other_info)
                + "</div>"
            )
        html_content += "</div>"

        return html_content

    def _entry_to_html(self, entry: Dict) -> str:
        html_content = "<div class='entry'>"
        html_content += "<div class='entry-header'>"
        if "company" in entry:
            html_content += (
                f"<span class='company'>{html.escape(entry['company'])}</span>"
            )
        if "date" in entry:
            html_content += f"<span class='date'>{html.escape(entry['date'])}</span>"
        html_content += "</div>"
        if "title" in entry:
            html_content += f"<div class='title'>{html.escape(entry['title'])}</div>"
        if "location" in entry:
            html_content += (
                f"<div class='location'>{html.escape(entry['location'])}</div>"
            )
        if "bullet_points" in entry:
            html_content += "<ul class='bullet-points'>"
            for point in entry["bullet_points"]:
                html_content += f"<li>{html.escape(point)}</li>"
            html_content += "</ul>"
        html_content += "</div>"
        return html_content

    def _list_to_html(self, list_item: Dict) -> str:
        html_content = f"<div class='list-group'><span class='list-group-title'>{html.escape(list_item['group'])}:</span> "
        enabled_items = [i["text"] for i in list_item["items"] if i["enabled"]]
        html_content += html.escape(", ".join(enabled_items))
        html_content += "</div>"
        return html_content


if __name__ == "__main__":
    resume = Resume("full_resume.txt")
    print(resume.to_text())
    print(resume.to_dict())
