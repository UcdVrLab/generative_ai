from diffusers.pipelines.shap_e.renderer import MeshDecoderOutput
import torch
import numpy as np

class Mesh:
    def __init__(self, mesh: MeshDecoderOutput = None) -> None:
        if not mesh: return
        if len(mesh.verts) > 65535: raise Exception("Mesh has too many vertices")
        self.verts:np.ndarray = mesh.verts.cpu().numpy()
        self.faces:np.ndarray = mesh.faces.cpu().numpy().astype(np.uint16)
        zipped_colors = torch.stack(list(mesh.vertex_channels.values()), dim=1)
        self.vert_colors:np.ndarray = (zipped_colors * 255).round().cpu().numpy().astype(np.uint8)
    
    def to_bytes(self):
        nv = len(self.verts).to_bytes(2, byteorder='little', signed=False) # uint16 - LE
        v = self.verts.tobytes() # float32 - LE
        vc = self.vert_colors.tobytes() # uint8 - LE
        nf = len(self.faces).to_bytes(4, byteorder='little', signed=False) # uint32 - LE
        f = self.faces.tobytes() # uint16 - LE
        return nv + v + vc + nf + f

    def from_bytes(bytes):
        mesh = Mesh()
        nv = int.from_bytes(bytes[0:2], byteorder='little', signed=False)
        v_size = nv*4*3
        vc_size = nv*1*3
        mesh.verts = np.frombuffer(bytes[2:2+v_size], dtype=np.float32).reshape(nv, 3)
        mesh.vert_colors = np.frombuffer(bytes[2+v_size:2+v_size+vc_size], dtype=np.uint8).reshape(nv, 3)
        nf = int.from_bytes(bytes[2+v_size+vc_size:6+v_size+vc_size], byteorder='little', signed=False)
        f_size = nf*2*3
        mesh.faces = np.frombuffer(bytes[6+v_size+vc_size:6+v_size+vc_size+f_size], dtype=np.uint16).reshape(nf, 3)
        return mesh
    
    def __eq__(self, other):
        if isinstance(other, Mesh):
            return (self.verts == other.verts).all() and (self.faces == other.faces).all() and (self.vert_colors == other.vert_colors).all()
        else: return False