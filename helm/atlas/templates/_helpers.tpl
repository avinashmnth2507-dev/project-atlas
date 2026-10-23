{{/* Shared application labels; keep selectors aligned with the Kustomize baseline. */}}
{{- define "atlas.labels" -}}
app.kubernetes.io/name: atlas-api
app.kubernetes.io/component: api
app.kubernetes.io/part-of: project-atlas
{{- end -}}

{{/* Compose an image reference from a repository and a required SHA-256 digest. */}}
{{- define "atlas.image" -}}
{{- $repository := required "image.repository is required" .Values.image.repository -}}
{{- $digest := required "image.digest is required" .Values.image.digest -}}
{{- if not (regexMatch "^sha256:[a-f0-9]{64}$" $digest) -}}
{{- fail "image.digest must be a lowercase sha256 digest" -}}
{{- end -}}
{{ printf "%s@%s" $repository $digest }}
{{- end -}}
