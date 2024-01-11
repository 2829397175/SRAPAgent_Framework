import os
import shutil

def generate_latex_for_images(pics,):
    latex_code = ""
    for i in range(0, len(pics), 2):
        # 开始一行
        latex_code += "\\begin{figure}[h]\n"
        latex_code += "\\centering\n"

        # 第一张图片
        latex_code += "\\subfloat["+pics[i]["caption"] +"]\n"
        latex_code += "{\\centering\n"
        latex_code += "\\includegraphics[width=.5\\linewidth]{" + pics[i]["path"] + "}\n"
        latex_code += "}\n"

        # 如果存在第二张图片
        if i+1 < len(pics):
            latex_code += "\\subfloat["+pics[i+1]["caption"] +"]\n"
            latex_code += "{\\centering\n"
            latex_code += "\\includegraphics[width=.5\\linewidth]{" + pics[i+1]["path"] + "}\n"
            latex_code += "}\n"

        # 结束一行
        latex_code += "\\end{figure}\n\n"

    return latex_code





if __name__ == "__main__":
    # root_dir = "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_new_priority_label/global_evaluation/visualize_priority_rating"
    root_dir = "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_new_priority_label/global_evaluation/visualize_priority_rating_weights"
    root_dir = "/data/jiarui_ji/publicHousing/LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_new_priority_perpersonlabel/global_evaluation/visualize_priority_rating_weights"
    pic_dirs = os.listdir(root_dir)
    save_dir = os.path.join(root_dir,"priority_weights")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    pics = []
    for pic_dir in pic_dirs:
        pic_dir = os.path.join(root_dir,pic_dir)
        if not os.path.isdir(pic_dir) or \
            pic_dir == save_dir:
            continue
        pic_paths = os.listdir(pic_dir)
        for pic_path in pic_paths:
            pic_path_ = os.path.join(pic_dir,pic_path)
            
            caption = pic_path.split(".")[0]
            if "non" in caption:
                caption = " ".join(caption.split("_")[:-2])
                caption = caption + " weights for non-vulnerable groups"
            else:
                caption = " ".join(caption.split("_")[:-1]) + " weights for vulnerable groups"
                
            pics.append({
                "path":f"figures/priority_weights/{pic_path}",
                "caption":caption
            })
            dst_path = os.path.join(save_dir,pic_path)
            shutil.copyfile(pic_path_,dst_path)
    
    # # 示例数据
    # pics = [
    #     {"path": "path/to/image1.jpg", "caption": "Image 1 Caption"},
    #     {"path": "path/to/image2.jpg", "caption": "Image 2 Caption"},
    #     # 添加更多图片和标题
    # ]

    latex_code = generate_latex_for_images(pics)
    with open(os.path.join(root_dir,"latex.txt"),"w") as f:
        f.write(latex_code)
    # print(latex_code)
