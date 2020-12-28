if gitlab.mr_body.length < 5
  fail "Please provide a summary in the Merge Request description."
end

# Let people say that this isn't worth a CHANGELOG entry in the PR if they choose
declared_trivial = (gitlab.mr_title + gitlab.mr_body).include?("#trivial")

if !git.modified_files.include?("CHANGELOG.md") && !declared_trivial
  fail("Please include a CHANGELOG entry. You can find it at [CHANGELOG.md](https://gitlab.com/eclipse-expeditions/aa-blueprints/-/blob/master/CHANGELOG.md).", sticky: false)
end

has_app_changes = !git.modified_files.grep(/^blueprints\/(?!tests\/)(.*)\.py/).empty?

has_test_changes = !git.modified_files.grep(/^blueprints\/tests/).empty?

if has_app_changes && !has_test_changes && git.lines_of_code > 20
  warn("Tests were not updated!", sticky: false)
end

has_po_changes = !git.modified_files.grep(/^blueprints\/locale\/([a-zA-Z_-]+)\/LC_MESSAGES\/django.po/).empty?

has_mo_changes = !git.modified_files.grep(/^blueprints\/locale\/([a-zA-Z_-]+)\/LC_MESSAGES\/django.mo/).empty?

if has_po_changes && !has_mo_changes
  fail("Please compile altered language files using `make compilemessages`.", sticky: false)
end
