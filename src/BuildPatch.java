import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import org.objectweb.asm.*;
public class BuildPatch {
  static int changed = 0;
  static byte[] patch(byte[] bytes, final String name, final String descriptor, final boolean path) {
    ClassReader reader = new ClassReader(bytes);
    ClassWriter writer = new ClassWriter(0);
    reader.accept(new ClassVisitor(Opcodes.ASM9, writer) {
      public MethodVisitor visitMethod(int access, String n, String d, String signature, String[] exceptions) {
        MethodVisitor mv = super.visitMethod(access,n,d,signature,exceptions);
        if (!n.equals(name) || !d.equals(descriptor)) return mv;
        changed++;
        mv.visitCode();
        boolean tip = name.equals("setTipTime");
        if(tip) { mv.visitVarInsn(Opcodes.ALOAD,0); mv.visitVarInsn(Opcodes.ILOAD,1); }
        else if(path) mv.visitVarInsn(Opcodes.ALOAD,1);
        mv.visitMethodInsn(Opcodes.INVOKESTATIC,"cloudinspect/macos/MacSupport",tip?"setTipTime":path?"openFile":"clientUpdate",tip?"(Ljavafx/scene/control/Tooltip;I)V":path?"(Ljava/lang/String;)V":"()V",false);
        mv.visitInsn(Opcodes.RETURN);
        mv.visitMaxs(tip?2:path?1:0,2);
        mv.visitEnd();
        return null;
      }
    },0);
    return writer.toByteArray();
  }
  public static void main(String[] args) throws Exception {
    try (ZipFile in = new ZipFile(args[0]); ZipOutputStream out = new ZipOutputStream(Files.newOutputStream(Paths.get(args[1])))) {
      Enumeration<? extends ZipEntry> entries=in.entries();
      while(entries.hasMoreElements()) {
        ZipEntry entry=entries.nextElement();
        byte[] b;
        try(java.io.InputStream s=in.getInputStream(entry);java.io.ByteArrayOutputStream buf=new java.io.ByteArrayOutputStream()) {
          byte[] chunk=new byte[8192];int n;while((n=s.read(chunk))!=-1)buf.write(chunk,0,n);b=buf.toByteArray();
        }
        if(entry.getName().equals("nc/cloudinspect/ui/utils/Director.class")) b=patch(b,"openFile","(Ljava/lang/String;)V",true);
        if(entry.getName().equals("nc/cloudinspect/service/update/VersionUpdate.class")) b=patch(b,"clientUpdate","(Lcom/alibaba/fastjson/JSONObject;)V",false);
        if(entry.getName().equals("nc/cloudinspect/ui/utils/InterfaceUtils.class")) b=patch(b,"setTipTime","(Ljavafx/scene/control/Tooltip;I)V",false);
        out.putNextEntry(new ZipEntry(entry.getName()));out.write(b);out.closeEntry();
      }
    }
    if(changed!=3) throw new IllegalStateException("Expected 3 methods, got "+changed);
    System.out.println("Patched exactly 3 macOS integration methods");
  }
}
