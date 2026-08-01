# Governance rules for the Acme telemetry schema.
#
# These are enforced by `weaver registry check --policy semconv/policies` and
# run in CI, so a schema change that breaks naming or documentation rules fails
# the build the same way a compile error would.
package before_resolution

# Every attribute defined by this registry (as opposed to one imported from the
# OpenTelemetry semantic conventions) must live under the `acme.` namespace, so
# that vendor attributes can never be confused with upstream ones.
deny contains attr_registry_namespace_violation(group.id, attr.id) if {
	group := input.groups[_]
	attr := group.attributes[_]
	attr.id
	not startswith(attr.id, "acme.")
}

# An attribute without a brief is undocumented telemetry. Reject it at the
# source rather than discovering it in a dashboard six months later.
deny contains attr_missing_brief_violation(group.id, attr.id) if {
	group := input.groups[_]
	attr := group.attributes[_]
	attr.id
	not attr.brief
}

attr_registry_namespace_violation(group_id, attr_id) := violation if {
	violation := {
		"id": sprintf("acme_namespace/%s", [attr_id]),
		"type": "semconv_attribute",
		"category": "naming",
		"group": group_id,
		"attr": attr_id,
		"brief": sprintf("Attribute '%s' in group '%s' must be defined under the 'acme.' namespace.", [attr_id, group_id]),
	}
}

attr_missing_brief_violation(group_id, attr_id) := violation if {
	violation := {
		"id": sprintf("acme_brief/%s", [attr_id]),
		"type": "semconv_attribute",
		"category": "documentation",
		"group": group_id,
		"attr": attr_id,
		"brief": sprintf("Attribute '%s' in group '%s' must have a non-empty brief.", [attr_id, group_id]),
	}
}
