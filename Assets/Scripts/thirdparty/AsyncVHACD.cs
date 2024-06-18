using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using UnityEngine;
using Mesh = Dummies.Mesh;

namespace MeshProcess {
    public static class AsyncVHACD {
        public struct Parameters {
            public double m_concavity;
            public double m_alpha;
            public double m_beta;
            public double m_minVolumePerCH;
            public unsafe void* m_callback;
            public unsafe void* m_logger;
            public uint m_resolution;
            public uint m_maxNumVerticesPerCH;
            public uint m_planeDownsampling;
            public uint m_convexhullDownsampling;
            public uint m_pca;
            public uint m_mode;
            public uint m_convexhullApproximation;
            public uint m_oclAcceleration;
            public uint m_maxConvexHulls;
            public bool m_projectHullVertices;

            public unsafe void Init() {
                m_resolution = 100000u;
                m_concavity = 0.001;
                m_planeDownsampling = 4u;
                m_convexhullDownsampling = 4u;
                m_alpha = 0.05;
                m_beta = 0.05;
                m_pca = 0u;
                m_mode = 0u;
                m_maxNumVerticesPerCH = 64u;
                m_minVolumePerCH = 0.0001;
                m_callback = null;
                m_logger = null;
                m_convexhullApproximation = 1u;
                m_oclAcceleration = 0u;
                m_maxConvexHulls = 1024u;
                m_projectHullVertices = true;
            }
        }

        private struct ConvexHull {
            public unsafe double* m_points;
            public unsafe uint* m_triangles;
            public uint m_nPoints;
            public uint m_nTriangles;
            public double m_volume;
            public unsafe fixed double m_center[3];
        }

        public static Parameters m_parameters;

        [DllImport("libvhacd")]
        private unsafe static extern void* CreateVHACD();

        [DllImport("libvhacd")]
        private unsafe static extern void DestroyVHACD(void* pVHACD);

        [DllImport("libvhacd")]
        private unsafe static extern bool ComputeFloat(void* pVHACD, float* points, uint countPoints, uint* triangles, uint countTriangles, Parameters* parameters);

        [DllImport("libvhacd")]
        private unsafe static extern bool ComputeDouble(void* pVHACD, double* points, uint countPoints, uint* triangles, uint countTriangles, Parameters* parameters);

        [DllImport("libvhacd")]
        private unsafe static extern uint GetNConvexHulls(void* pVHACD);

        [DllImport("libvhacd")]
        private unsafe static extern void GetConvexHull(void* pVHACD, uint index, ConvexHull* ch);

        static AsyncVHACD() {
            m_parameters.Init();
        }

        public static unsafe List<Mesh> GenerateConvexMeshes(Mesh mesh) {
            void* pVHACD = CreateVHACD();
            Parameters parameters = m_parameters;
            Vector3[] vertices = mesh.Vertices;
            int[] triangles = mesh.Faces;
            fixed (Vector3* points = vertices) {
                fixed (int* triangles2 = triangles) {
                    ComputeFloat(pVHACD, (float*)points, (uint)vertices.Length, (uint*)triangles2, (uint)triangles.Length / 3u, &parameters);
                }
            }
            List<Mesh> list = new();
            ConvexHull convexHull = default;
            foreach (int i in Enumerable.Range(0, (int)GetNConvexHulls(pVHACD))) {
                GetConvexHull(pVHACD, (uint)i, &convexHull);
                Mesh mesh2 = new();
                Vector3[] array = new Vector3[convexHull.m_nPoints];
                fixed (Vector3* ptr2 = array) {
                    double* ptr = convexHull.m_points;
                    Vector3* ptr3 = ptr2;
                    for (uint num = convexHull.m_nPoints; num != 0; num--) {
                        ptr3->x = (float)*ptr;
                        ptr3->y = (float)ptr[1];
                        ptr3->z = (float)ptr[2];
                        ptr3++;
                        ptr += 3;
                    }
                }

                mesh2.Vertices = array;
                int[] array2 = new int[convexHull.m_nTriangles * 3];
                Marshal.Copy((IntPtr)convexHull.m_triangles, array2, 0, array2.Length);
                mesh2.Faces = array2;
                list.Add(mesh2);
            }

            return list;
        }
    }
}