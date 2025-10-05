import { z } from "zod";

// Base types
export const BBoxSchema = z.object({
  x: z.number(),
  y: z.number(),
  width: z.number(),
  height: z.number(),
});

export const PointSchema = z.object({
  x: z.number(),
  y: z.number(),
});

export const PolygonSchema = z.object({
  points: z.array(PointSchema),
});

// Dataset schemas
export const DatasetSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  tileType: z.enum(["dzi", "tms", "iiif"]).default("dzi"),
  tileUrl: z.string(),
  levels: z.array(z.number()),
  pixelSize: z.tuple([z.number(), z.number()]),
  metadata: z.record(z.any()).optional(),
  createdAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
});

export const DatasetListSchema = z.array(DatasetSchema);

// Overlay schemas
export const OverlayPositionSchema = z.object({
  x: z.number(),
  y: z.number(),
  width: z.number().positive(),
  rotation: z.number().default(0),
});

export const OverlaySchema = z.object({
  id: z.string(),
  datasetId: z.string(),
  sourceDatasetId: z.string().optional(),
  name: z.string(),
  tileUrl: z.string(),
  opacity: z.number().min(0).max(1),
  visible: z.boolean(),
  position: OverlayPositionSchema,
  metadata: z.record(z.any()).optional(),
  createdAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
});

export const OverlayListSchema = z.array(OverlaySchema);

// Feature schemas
export const FeatureSchema = z.object({
  id: z.string(),
  datasetId: z.string(),
  name: z.string(),
  type: z.enum(["point", "bbox", "polygon"]),
  geometry: z.union([PointSchema, BBoxSchema, PolygonSchema]),
  properties: z.record(z.any()).optional(),
  createdAt: z.string().datetime().optional(),
});

export const FeatureListSchema = z.array(FeatureSchema);

// Annotation schemas
export const AnnotationSchema = z.object({
  id: z.string(),
  datasetId: z.string(),
  userId: z.string().optional(),
  type: z.enum(["point", "rect", "polygon"]),
  geometry: z.union([PointSchema, BBoxSchema, PolygonSchema]),
  label: z.string().optional(),
  description: z.string().optional(),
  color: z.string().optional(),
  metadata: z.record(z.any()).optional(),
  createdAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
});

export const CreateAnnotationSchema = z.object({
  datasetId: z.string(),
  type: z.enum(["point", "rect", "polygon"]),
  geometry: z.union([PointSchema, BBoxSchema, PolygonSchema]),
  label: z.string().optional(),
  description: z.string().optional(),
  color: z.string().optional(),
  metadata: z.record(z.any()).optional(),
});

export const UpdateAnnotationSchema = z.object({
  geometry: z.union([PointSchema, BBoxSchema, PolygonSchema]).optional(),
  label: z.string().optional(),
  description: z.string().optional(),
  color: z.string().optional(),
  metadata: z.record(z.any()).optional(),
});

export const AnnotationListSchema = z.array(AnnotationSchema);

// Search schemas
export const SearchResultSchema = z.object({
  bbox: BBoxSchema,
  score: z.number(),
  preview: z.string().optional(),
  metadata: z.record(z.any()).optional(),
});

export const SearchResponseSchema = z.object({
  query: z.string(),
  datasetId: z.string(),
  results: z.array(SearchResultSchema),
  total: z.number(),
});

export const OverlayStatusSchema = z.object({
  overlayId: z.string(),
  status: z.enum(["queued", "processing", "complete", "error"]),
  progress: z.number().min(0).max(100),
  message: z.string(),
  result: z.record(z.any()).optional(),
});

// Auth schemas
export const LoginSchema = z.object({
  username: z.string(),
  password: z.string(),
});

export const TokenSchema = z.object({
  accessToken: z.string(),
  tokenType: z.string().default("bearer"),
});

// Health check
export const HealthSchema = z.object({
  status: z.enum(["ok", "degraded", "down"]),
  version: z.string().optional(),
  timestamp: z.string().datetime(),
});

// Type exports
export type BBox = z.infer<typeof BBoxSchema>;
export type Point = z.infer<typeof PointSchema>;
export type Polygon = z.infer<typeof PolygonSchema>;
export type Dataset = z.infer<typeof DatasetSchema>;
export type DatasetList = z.infer<typeof DatasetListSchema>;
export type OverlayPosition = z.infer<typeof OverlayPositionSchema>;
export type Overlay = z.infer<typeof OverlaySchema>;
export type OverlayList = z.infer<typeof OverlayListSchema>;
export type Feature = z.infer<typeof FeatureSchema>;
export type FeatureList = z.infer<typeof FeatureListSchema>;
export type Annotation = z.infer<typeof AnnotationSchema>;
export type CreateAnnotation = z.infer<typeof CreateAnnotationSchema>;
export type UpdateAnnotation = z.infer<typeof UpdateAnnotationSchema>;
export type AnnotationList = z.infer<typeof AnnotationListSchema>;
export type SearchResult = z.infer<typeof SearchResultSchema>;
export type SearchResponse = z.infer<typeof SearchResponseSchema>;
export type OverlayStatus = z.infer<typeof OverlayStatusSchema>;
export type Login = z.infer<typeof LoginSchema>;
export type Token = z.infer<typeof TokenSchema>;
export type Health = z.infer<typeof HealthSchema>;
