if gitlab.mr_body.length < 5
  fail "Please provide a summary in the Pull Request description"
end

# Let people say that this isn't worth a CHANGELOG entry in the PR if they choose
declared_trivial = (gitlab.mr_title + gitlab.mr_body).include?("#trivial")

if !git.modified_files.include?("CHANGELOG.md") && !declared_trivial
  fail("Please include a CHANGELOG entry. You can find it at [CHANGELOG.md](https://gitlab.com/eclipse-expeditions/aa-blueprints/-/blob/master/CHANGELOG.md).", sticky: false)
end
